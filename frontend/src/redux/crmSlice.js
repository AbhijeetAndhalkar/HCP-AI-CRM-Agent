import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  hcpName: '',
  interactionType: '',
  date: '',
  time: '',
  attendees: '',
  topicsDiscussed: '',
  materialsShared: '',
  sentiment: '',
  outcomes: '',
  followUpActions: '',
  suggestedFollowUps: [],
  chatMessages: [],
};

export const crmSlice = createSlice({
  name: 'crm',
  initialState,
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      if (state[field] !== undefined) {
        state[field] = value;
      }
    },
    updateFormData: (state, action) => {
      return { ...state, ...action.payload };
    },
    addChatMessage: (state, action) => {
      state.chatMessages.push(action.payload);
    },
    addSuggestedFollowUp: (state, action) => {
      state.suggestedFollowUps.push(action.payload);
    }
  },
});

export const { updateFormField, updateFormData, addChatMessage, addSuggestedFollowUp } = crmSlice.actions;

export default crmSlice.reducer;
