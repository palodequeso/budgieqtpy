import { createNativeStackNavigator } from '@react-navigation/native-stack';
import BudgetScreen from '../screens/BudgetScreen';
import BudgetItemForm from '../screens/BudgetItemForm';
import { BudgetGroup, BudgetItem } from '../store/store';

export type BudgetStackParamList = {
  BudgetList: undefined;
  BudgetItemForm: { groups: BudgetGroup[]; item?: BudgetItem };
};

const Stack = createNativeStackNavigator<BudgetStackParamList>();

export default function BudgetStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="BudgetList" component={BudgetScreen} />
      <Stack.Screen name="BudgetItemForm" component={BudgetItemForm} />
    </Stack.Navigator>
  );
}
