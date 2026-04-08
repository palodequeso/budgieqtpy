import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, Snackbar, Dialog, Portal, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AccountsStackParamList } from '../navigation/AccountsStack';
import { api } from '../api/api';
import { useStore, Profile } from '../store/store';

type Props = NativeStackScreenProps<AccountsStackParamList, 'LedgerForm'>;

export default function LedgerForm({ route, navigation }: Props) {
  const { accountId, profileId, ledgerEntry } = route.params;
  const isEdit = !!ledgerEntry;
  const theme = useTheme();
  const today = new Date().toISOString().split('T')[0];

  const [amount, setAmount] = useState(ledgerEntry?.amount.toString() ?? '');
  const [notes, setNotes] = useState(ledgerEntry?.name ?? '');
  const [date, setDate] = useState(ledgerEntry?.paid_date ?? today);
  const [incomeDate, setIncomeDate] = useState(ledgerEntry?.income_date ?? today);
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState('');
  const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSave = async () => {
    if (!amount || isNaN(parseFloat(amount))) {
      setSnackbar('Amount is required and must be a number');
      return;
    }
    if (!date || !incomeDate) {
      setSnackbar('Both dates are required');
      return;
    }

    setSaving(true);
    try {
      const body = {
        account_id: accountId,
        amount: parseFloat(amount),
        date: date,
        income_date: incomeDate,
        notes: notes || undefined,
      };

      if (!isEdit) {
        await api.post(`/ledger/${profileId}`, body);
      } else {
        await api.put(`/ledger/${profileId}/${ledgerEntry!.id}`, body);
      }

      const profile = await api.get<Profile>(`/profiles/${profileId}`);
      useStore.getState().setAccounts(profile.accounts);

      setSnackbar(isEdit ? 'Entry updated' : 'Entry created');
      setTimeout(() => navigation.goBack(), 600);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save entry');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!ledgerEntry) return;
    setDeleting(true);
    try {
      await api.del(`/ledger/${profileId}/${ledgerEntry.id}`);
      const profile = await api.get<Profile>(`/profiles/${profileId}`);
      useStore.getState().setAccounts(profile.accounts);
      setDeleteDialogVisible(false);
      setSnackbar('Entry deleted');
      setTimeout(() => navigation.goBack(), 600);
    } catch (e: any) {
      setDeleteDialogVisible(false);
      setSnackbar(e.message ?? 'Failed to delete entry');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={[styles.container, { backgroundColor: theme.colors.background }]} keyboardShouldPersistTaps="handled">
          <Text variant="titleLarge" style={styles.title}>
            {isEdit ? 'Edit Entry' : 'Add Entry'}
          </Text>

          <TextInput
            label="Amount"
            value={amount}
            onChangeText={setAmount}
            mode="outlined"
            keyboardType="decimal-pad"
            style={styles.input}
          />

          <TextInput
            label="Notes"
            value={notes}
            onChangeText={setNotes}
            mode="outlined"
            style={styles.input}
          />

          <TextInput
            label="Date (YYYY-MM-DD)"
            value={date}
            onChangeText={setDate}
            mode="outlined"
            style={styles.input}
          />

          <TextInput
            label="Income Date (YYYY-MM-DD)"
            value={incomeDate}
            onChangeText={setIncomeDate}
            mode="outlined"
            style={styles.input}
          />

          <Button
            mode="contained"
            onPress={handleSave}
            loading={saving}
            disabled={saving}
            style={styles.button}
          >
            {isEdit ? 'Save Changes' : 'Add Entry'}
          </Button>

          {isEdit && (
            <Button
              mode="outlined"
              onPress={() => setDeleteDialogVisible(true)}
              style={[styles.deleteButton, { borderColor: theme.colors.error }]}
              textColor={theme.colors.error}
            >
              Delete Entry
            </Button>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      <Snackbar
        visible={!!snackbar}
        onDismiss={() => setSnackbar('')}
        duration={3000}
      >
        {snackbar}
      </Snackbar>

      <Portal>
        <Dialog visible={deleteDialogVisible} onDismiss={() => setDeleteDialogVisible(false)}>
          <Dialog.Title>Delete Entry</Dialog.Title>
          <Dialog.Content>
            <Text>Delete this ledger entry? This cannot be undone.</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteDialogVisible(false)}>Cancel</Button>
            <Button onPress={handleDelete} textColor={theme.colors.error} loading={deleting} disabled={deleting}>Delete</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  container: {
    padding: 16,
    flexGrow: 1,
  },
  title: { marginBottom: 24 },
  input: { marginBottom: 12 },
  button: { marginTop: 16 },
  deleteButton: { marginTop: 12 },
});
