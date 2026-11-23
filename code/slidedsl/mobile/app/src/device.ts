import * as Device from 'expo-device';
import * as Battery from 'expo-battery';
import {Platform} from 'react-native';
export async function deviceSnapshot() {
  const [level, state, power] = await Promise.allSettled([
    Battery.getBatteryLevelAsync(), Battery.getBatteryStateAsync(), Battery.isLowPowerModeEnabledAsync(),
  ]);
  const battery = level.status === 'fulfilled' && level.value >= 0 ? level.value : null;
  return {recorded_at: new Date().toISOString(), model: Device.modelName, manufacturer: Device.manufacturer,
    ram_bytes: Device.totalMemory, android: Platform.OS === 'android' ? Platform.Version : null,
    os_version: Device.osVersion, is_device: Device.isDevice,
    battery_level: battery, battery_state: state.status === 'fulfilled' ? state.value : null,
    low_power: power.status === 'fulfilled' ? power.value : null,
    temperature_c: null, temperature_unavailable_reason: 'Expo Battery não expõe temperatura.'};
}