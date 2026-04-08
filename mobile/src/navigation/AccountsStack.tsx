import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AccountsScreen from '../screens/AccountsScreen';
import AccountLedger from '../screens/AccountLedger';
import LedgerForm from '../screens/LedgerForm';
import AccountForm from '../screens/AccountForm';
import { Account } from '../store/store';

export type AccountsStackParamList = {
  AccountsList: undefined;
  AccountLedger: { account: { id: number; name: string; type: string; balance: number } };
  LedgerForm: { accountId: number; profileId: number; ledgerEntry?: import('../store/store').LedgerEntry };
  AccountForm: { account?: Account; profileId: number };
};

const Stack = createNativeStackNavigator<AccountsStackParamList>();

export default function AccountsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="AccountsList" component={AccountsScreen} />
      <Stack.Screen name="AccountLedger" component={AccountLedger} />
      <Stack.Screen name="LedgerForm" component={LedgerForm} />
      <Stack.Screen name="AccountForm" component={AccountForm} />
    </Stack.Navigator>
  );
}
