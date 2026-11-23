const path = require('path');
const fs = require('fs');
const {getDefaultConfig} = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
// Core is mirrored next to app; JSON font tables are ordinary bundle modules.
config.watchFolders = [path.resolve(__dirname, '../slidedsl-core')];
config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];
config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];
const upstreamResolve = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  // Node ESM uses .js specifiers in TS sources; Metro needs the source extension.
  // Existing .js files in core/dist retain their normal resolution.
  if (moduleName.startsWith('.') && moduleName.endsWith('.js')) {
    const target = path.resolve(path.dirname(context.originModulePath), moduleName);
    if (!fs.existsSync(target) && fs.existsSync(target.slice(0, -3) + '.ts')) {
      moduleName = moduleName.slice(0, -3) + '.ts';
    }
  }
  return upstreamResolve ? upstreamResolve(context, moduleName, platform) : context.resolveRequest(context, moduleName, platform);
};
module.exports = config;