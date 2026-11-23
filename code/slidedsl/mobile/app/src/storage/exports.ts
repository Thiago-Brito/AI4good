import {File, Paths} from 'expo-file-system';
import * as FS from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
export const PPTX_MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
export async function storePptx(bytes: ArrayBuffer): Promise<string> {
  const file = new File(Paths.document, `SlideDSL-${Date.now()}.pptx`);
  file.create({overwrite: true});
  await file.write(new Uint8Array(bytes));
  return file.uri;
}
export async function shareFile(uri: string, mimeType: string): Promise<void> {
  if (!await Sharing.isAvailableAsync()) throw Error('Compartilhamento indisponível neste aparelho.');
  await Sharing.shareAsync(uri, {mimeType, dialogTitle: 'Compartilhar SlideDSL', UTI: mimeType === PPTX_MIME ? 'org.openxmlformats.presentationml.presentation' : 'public.json'});
}
export async function savePptx(uri: string): Promise<boolean> {
  const permission = await FS.StorageAccessFramework.requestDirectoryPermissionsAsync();
  if (!permission.granted) return false;
  const name = uri.split('/').pop() ?? 'SlideDSL.pptx';
  const destination = await FS.StorageAccessFramework.createFileAsync(permission.directoryUri, name, PPTX_MIME);
  const bytes = await FS.readAsStringAsync(uri, {encoding: FS.EncodingType.Base64});
  await FS.writeAsStringAsync(destination, bytes, {encoding: FS.EncodingType.Base64});
  return true;
}
export async function exportTestData(data: unknown): Promise<void> {
  const file = new File(Paths.document, `SlideDSL-teste-${Date.now()}.json`);
  file.create({overwrite: true});
  await file.write(JSON.stringify(data, null, 2));
  await shareFile(file.uri, 'application/json');
}