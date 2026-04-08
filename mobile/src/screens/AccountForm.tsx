import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, Button, Snackbar, Dialog, Portal, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AccountsStackParamList } from '../navigation/AccountsStack';
import { useStore, Profile } from '../store/store';
import { api } from '../api/api';

type Props = NativeStackScreenProps<AccountsStackParamList, 'AccountForm'>;

export default function AccountForm({ route, navigation }: Props) {
  const { account, profileId } = route.params;
  const isEdit = !!account;
  const { setAccounts } = useStore();
  const theme = useTheme();

  const [name, setName] = useState(account?.name ?? '');
  const [type, setType] = useState(account?.type ?? 'checking');
  const [balance, setBalance] = useState(account?.balance?.toString() ?? '0');
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState('');
  const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const refreshStore = async () => {
    const profile = await api.get<Profile>(`/profiles/${profileId}`);
    setAccounts(profile.accounts);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setSnackbar('Name is required');
      return;
    }
    if (isNaN(parseFloat(balance))) {
      setSnackbar('Balance must be a number');
      return;
    }
    setSaving(true);
    try {
      const body = { name: name.trim(), type: type.trim() || 'checking', balance: parseFloat(balance) };
      if (isEdit) {
        await api.put(`/accounts/${profileId}/${account!.id}`, body);
      } else {
        await api.post(`/accounts/${profileId}`, body);
      }
      await refreshStore();
      setSnackbar(isEdit ? 'Account updated' : 'Account created');
      setTimeout(() => navigation.goBack(), 600);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save account');
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={[styles.container, { backgroundColor: theme.colors.background }]} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Button icon="arrow-left" mode="text" onPress={() => navigation.goBack()} style={styles.backButton}>
              Back
            </Button>
            <Text variant="titleLarge">{isEdit ? 'Edit Account' : 'New Account'}</Text>
          </View>

          <TextInput label="Name" value={name} onChangeText={setName} mode="outlined" style={styles.input} />
          <TextInput
            label="Type (e.g. checking, savings, credit)"
            value={type}
            onChangeText={setType}
            mode="outlined"
            autoCapitalize="none"
            style={styles.input}
          />
          <TextInput
            label="Balance"
            value={balance}
            onChangeText={setBalance}
            mode="outlined"
            keyboardType="decimal-pad"
            style={styles.input}
          />

          <Button mode="contained" onPress={handleSave} loading={saving} disabled={saving} style={styles.saveButton}>
            {isEdit ? 'Save Changes' : 'Create Account'}
          </Button>
        </ScrollView>
      </KeyboardAvoidingView>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={3000}>{snackbar}</Snackbar>

      <Portal>
        <Dialog visible={deleteDialogVisible} onDismiss={() => setDeleteDialogVisible(false)}>
          <Dialog.Title>Delete Account</Dialog.Title>
          <Dialog.Content>
            <Text>Delete "{account?.name}"? This cannot be undone.</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteDialogVisible(false)}>Cancel</Button>
            <Button textColor={theme.colors.error} loading={deleting} disabled={deleting} onPress={async () => {
              setDeleting(true);
              // No delete endpoint in current API — show message
              setDeleteDialogVisible(false);
              setSnackbar('Account deletion not supported by server');
              setDeleting(false);
            }}>Delete</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  container: { padding: 16, flexGrow: 1 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: 20, gap: 8 },
  backButton: { marginLeft: -8 },
  input: { marginBottom: 12 },
  saveButton: { marginTop: 8 },
});
