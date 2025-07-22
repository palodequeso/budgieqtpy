import "jest-location-mock";

import * as zustand from 'zustand';

const { create: actualCreate, createStore: actualCreateStore } =
  jest.requireActual<typeof zustand>('zustand');

const createUncurried = <T>(stateCreator: zustand.StateCreator<T>) => {
    const store = actualCreate(stateCreator);
    const initialState = store.getState();
    // storeResetFns.add(() => {
    //     store.setState(initialState, true);
    // });
    return store;
}
