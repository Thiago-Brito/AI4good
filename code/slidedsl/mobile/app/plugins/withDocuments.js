const {withAndroidManifest} = require('expo/config-plugins');
const mimes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown', 'text/x-markdown'];
module.exports = function withDocuments(config) {
  return withAndroidManifest(config, mod => {
    const activities = mod.modResults.manifest.application[0].activity;
    const main = activities.find(a => a.$['android:name'] === '.MainActivity');
    if (!main) throw Error('MainActivity ausente.');
    main.$['android:launchMode'] = 'singleTask';
    // Idempotente: preserva filtros launcher/deep-link do Expo.
    main['intent-filter'] = (main['intent-filter'] ?? []).filter(f => !f.action?.some(a => ['android.intent.action.SEND', 'android.intent.action.VIEW'].includes(a.$['android:name'])));
    for (const action of ['SEND', 'VIEW']) main['intent-filter'].push({
      action: [{$: {'android:name': `android.intent.action.${action}`}}],
      category: [{$: {'android:name': 'android.intent.category.DEFAULT'}}],
      data: mimes.flatMap(mime => action === 'VIEW'
        ? ['content', 'file'].map(scheme => ({$: {'android:mimeType': mime, 'android:scheme': scheme}}))
        : [{$: {'android:mimeType': mime}}]),
    });
    return mod;
  });
};
