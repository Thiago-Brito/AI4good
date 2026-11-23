import type {ReactNode} from 'react';
import {Pressable, StyleSheet, Text} from 'react-native';
export function Button({children, onPress, disabled = false, secondary = false}: {children: ReactNode; onPress: () => void; disabled?: boolean; secondary?: boolean}) {
  return <Pressable accessibilityRole="button" accessibilityState={{disabled}} disabled={disabled} onPress={onPress}
    style={[styles.button, secondary && styles.secondary, disabled && styles.disabled]}>
    <Text style={[styles.buttonText, secondary && {color: '#14233D'}]}>{children}</Text>
  </Pressable>;
}
export const styles = StyleSheet.create({
  page: {padding: 20, paddingTop: 56, paddingBottom: 40, gap: 14, backgroundColor: '#F6F8FC', flexGrow: 1},
  title: {fontSize: 30, fontWeight: '700', color: '#14233D'},
  heading: {fontSize: 20, fontWeight: '600', color: '#14233D'},
  label: {fontSize: 16, fontWeight: '600', color: '#14233D'},
  text: {fontSize: 15, color: '#475467'},
  input: {minHeight: 54, borderWidth: 1, borderColor: '#D0D5DD', borderRadius: 12, padding: 12, fontSize: 16, backgroundColor: '#FFF', textAlignVertical: 'top'},
  row: {flexDirection: 'row', gap: 8, flexWrap: 'wrap'},
  card: {backgroundColor: '#FFF', borderWidth: 1, borderColor: '#D0D5DD', borderRadius: 12, padding: 14, gap: 10},
  button: {backgroundColor: '#14233D', borderRadius: 12, paddingVertical: 14, paddingHorizontal: 15, alignItems: 'center'},
  secondary: {backgroundColor: '#E3EAF4'}, disabled: {opacity: 0.4},
  buttonText: {color: '#FFF', fontSize: 16, fontWeight: '600'},
  error: {fontSize: 15, color: '#B42318'}, warning: {fontSize: 15, color: '#855600', backgroundColor: '#FFF4D6', padding: 10, borderRadius: 8},
});