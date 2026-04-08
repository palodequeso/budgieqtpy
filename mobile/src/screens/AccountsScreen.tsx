import React, { useState, useCallback } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, List, Divider, ActivityIndicator, Button, FAB, IconButton, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useStore, Account, Profile } from '../store/store';
import { api } from '../api/api';
import HelpIcon from '../components/HelpIcon';
import { AccountsStackParamList } from '../navigation/AccountsStack';

type Nav = NativeStackNavigationProp<AccountsStackParamList, 'AccountsList'>;

export default function AccountsScreen() {
  const navigation = useNavigation<Nav>();
  const { selectedProfileId, setAccounts: storeSetAccounts } = useStore();
  const theme = useTheme();

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAccounts = useCallback(async (isRefresh = false) => {
    if (!selectedProfileId) return;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const profile = await api.get<Profile>(`/profiles/${selectedProfileId}`);
      setAccounts(profile.accounts);
      storeSetAccounts(profile.accounts);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load accounts');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedProfileId, storeSetAccounts]);

  useFocusEffect(
    useCallback(() => {
      fetchAccounts();
    }, [fetchAccounts])
  );

  const balanceColor = (amount: number) => (amount < 0 ? theme.colors.error : '#66bb6a');

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
          <Text variant="titleLarge">Accounts</Text>
          <HelpIcon text="Add your bank accounts here. Each account tracks its own ledger of transactions." />
        </View>

        {!selectedProfileId ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            Select a profile in Settings to view accounts
          </Text>
        ) : loading && !refreshing ? (
          <ActivityIndicator animating color={theme.colors.primary} style={styles.loader} />
        ) : error ? (
          <View>
            <Text variant="bodySmall" style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
            <Button mode="outlined" onPress={() => fetchAccounts()} style={styles.retryButton}>Retry</Button>
          </View>
        ) : accounts.length === 0 && !loading ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No accounts yet.{'\n\n'}Accounts represent your bank accounts — checking, savings, credit cards. Each account has a ledger that tracks transactions.{'\n\n'}Tap the + button to create your first one.
          </Text>
        ) : (
          <ScrollView
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={() => fetchAccounts(true)} colors={[theme.colors.primary]} />
            }
          >
            {accounts.map((account, index) => (
              <React.Fragment key={account.id}>
                <List.Item
                  title={account.name}
                  description={account.type}
                  right={() => (
                    <View style={styles.rowRight}>
                      <Text style={[styles.balanceText, { color: balanceColor(account.balance) }]}>
                        {account.balance.toFixed(2)}
                      </Text>
                      <IconButton
                        icon="pencil"
                        size={18}
                        iconColor={theme.colors.onSurfaceVariant}
                        onPress={() =>
                          navigation.navigate('AccountForm', {
                            account,
                            profileId: selectedProfileId!,
                          })
                        }
                      />
                    </View>
                  )}
                  onPress={() =>
                    navigation.navigate('AccountLedger', {
                      account: { id: account.id, name: account.name, type: account.type, balance: account.balance },
                    })
                  }
                />
                {index < accounts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </ScrollView>
        )}
      </View>

      {selectedProfileId && (
        <FAB
          icon="plus"
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          color={theme.colors.background}
          onPress={() => navigation.navigate('AccountForm', { profileId: selectedProfileId! })}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  title: { marginBottom: 16 },
  loader: { marginTop: 32 },
  errorText: { marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  rowRight: { flexDirection: 'row', alignItems: 'center' },
  balanceText: { alignSelf: 'center', fontVariant: ['tabular-nums'], fontSize: 16 },
  fab: { position: 'absolute', right: 16, bottom: 16 },
});
