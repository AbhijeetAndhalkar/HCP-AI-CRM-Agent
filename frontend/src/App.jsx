import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { updateFormField, updateFormData, addChatMessage } from './redux/crmSlice';
import axios from 'axios';

function App() {
  const dispatch = useDispatch();
  const crmData = useSelector((state) => state.crm);
  const chatMessages = useSelector((state) => state.crm.chatMessages);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    dispatch(updateFormField({ field: name, value }));
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Add user message to chat (Redux state)
    dispatch(addChatMessage({ role: 'user', content: inputText }));
    
    // Construct memory array for the backend API
    const updatedHistory = [
      ...chatMessages.map(msg => ({
        role: msg.role === 'user' ? 'human' : 'ai',
        content: msg.content
      })),
      { role: "human", content: inputText }
    ];

    setInputText('');
    setLoading(true);

    try {
      // Send the ENTIRE history to the backend
      const response = await axios.post('http://localhost:8000/chat', {
        messages: updatedHistory
      });

      const responseData = response.data;
      
      let aiReplyStr = "";
      if (typeof responseData === 'string') {
          // If the string itself is a JSON representation, try parsing it
          try {
              const parsedStr = JSON.parse(responseData);
              if (parsedStr.response) {
                  aiReplyStr = parsedStr.response;
              } else {
                  aiReplyStr = responseData;
              }
          } catch(e) {
              aiReplyStr = responseData;
          }
      } else if (responseData.response) {
          aiReplyStr = responseData.response;
      } else if (responseData.reply) {
          aiReplyStr = responseData.reply;
      } else if (responseData.message) {
          aiReplyStr = responseData.message;
      } else if (responseData.content) {
          aiReplyStr = responseData.content;
      } else {
          aiReplyStr = JSON.stringify(responseData);
      }

      // Pre-process to unescape strings from backend
      const cleanReply = aiReplyStr.replace(/\\"/g, '"').replace(/\\n/g, '\n');

      let finalChatMsg = cleanReply;

      // 1. Try to find JSON between backticks (Standard)
      let jsonMatch = cleanReply.match(/```json\s*([\s\S]*?)\s*```/);

      // 2. SAFETY NET: If no backticks, try to find anything between curly braces
      if (!jsonMatch) {
          jsonMatch = cleanReply.match(/\{[\s\S]*?\}/);
      }

      if (jsonMatch) {
          try {
              // Use the first capture group if backticks were found, 
              // or the whole match if it's just braces.
              const jsonString = Array.isArray(jsonMatch) && jsonMatch[1] ? jsonMatch[1] : jsonMatch[0];
              const parsedData = JSON.parse(jsonString);
              
              const isValidValue = (val) => val && val !== "..." && val !== "Extract Name" && val !== "In-person OR Virtual" && val !== "Positive, Neutral, or Negative" && val !== "Summary of topics" && val !== "Materials shared" && val !== "Suggested tasks";

              if (parsedData.date) {
                if (parsedData.date.toLowerCase().includes("today") || 
                    parsedData.date.toLowerCase().includes("yesterday")) {
                    delete parsedData.date; // Let the AI ask for the real date instead
                }
              }

              const mappedData = {};
              if (isValidValue(parsedData.hcpName)) mappedData.hcpName = parsedData.hcpName;
              if (isValidValue(parsedData.interactionType)) mappedData.interactionType = parsedData.interactionType;
              if (isValidValue(parsedData.sentiment)) {
                  // Ensure proper case matching for the Radio Buttons
                  const s = parsedData.sentiment.trim();
                  mappedData.sentiment = s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
              }
              if (isValidValue(parsedData.date)) mappedData.date = parsedData.date;
              if (isValidValue(parsedData.topics)) mappedData.topicsDiscussed = parsedData.topics;
              if (isValidValue(parsedData.materials)) mappedData.materialsShared = parsedData.materials;
              if (isValidValue(parsedData.followUp)) mappedData.followUpActions = parsedData.followUp;

              // Dispatch update to Redux (merges cleanly without clearing existing data)
              dispatch(updateFormData(mappedData));
          } catch (err) {
              console.error("Failed to parse JSON even with safety net", err);
          }
      }

      // 3. Clean the chat UI (Remove the JSON block from the text bubble)
      const cleanVoiceReply = cleanReply.replace(/```json[\s\S]*?```/g, "").replace(/\{[\s\S]*?\}/g, "").trim();
      finalChatMsg = cleanVoiceReply;

      dispatch(addChatMessage({ role: 'ai', content: finalChatMsg || "I've processed your request." }));

    } catch (error) {
      console.error("Error communicating with backend:", error);
      dispatch(addChatMessage({ role: 'ai', content: "Error: Could not reach the server." }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex font-sans">
      {/* Left Column: CRM Form */}
      <div className="w-1/2 p-8 pb-32 border-r border-gray-200 overflow-y-auto h-screen bg-white shadow-sm">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Log HCP Interaction</h1>
          <p className="text-sm text-gray-500 mt-1">Interaction Details</p>
        </div>
        
        <form className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">HCP Name</label>
              <input type="text" name="hcpName" value={crmData.hcpName || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="e.g. Dr. Jane Smith" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Interaction Type</label>
              <input type="text" name="interactionType" value={crmData.interactionType || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="e.g. In-person, Virtual" />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input type="date" name="date" value={crmData.date || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
              <input type="time" name="time" value={crmData.time || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Attendees</label>
            <input type="text" name="attendees" value={crmData.attendees || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Other participants" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Topics Discussed</label>
            <textarea name="topicsDiscussed" value={crmData.topicsDiscussed || ''} onChange={handleInputChange} rows="3" className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Key topics covered..."></textarea>
            <div className="mt-2">
              <button type="button" className="inline-flex items-center text-sm text-gray-600 hover:text-blue-700 transition-colors bg-gray-50 hover:bg-gray-100 px-3 py-1.5 rounded-md border border-gray-200">
                <svg className="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
                Summarize from Voice Note <span className="text-xs ml-1 text-gray-400">(Requires Consent)</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Materials Shared</label>
              <input type="text" name="materialsShared" value={crmData.materialsShared || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Brochures, studies, etc." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sentiment</label>
              <div className="flex items-center space-x-5 mt-3">
                <label className="flex items-center text-sm text-gray-700 cursor-pointer">
                  <input type="radio" name="sentiment" value="Positive" checked={crmData.sentiment === 'Positive'} onChange={handleInputChange} className="mr-2 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" /> Positive
                </label>
                <label className="flex items-center text-sm text-gray-700 cursor-pointer">
                  <input type="radio" name="sentiment" value="Neutral" checked={crmData.sentiment === 'Neutral'} onChange={handleInputChange} className="mr-2 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" /> Neutral
                </label>
                <label className="flex items-center text-sm text-gray-700 cursor-pointer">
                  <input type="radio" name="sentiment" value="Negative" checked={crmData.sentiment === 'Negative'} onChange={handleInputChange} className="mr-2 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" /> Negative
                </label>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Outcomes</label>
            <textarea name="outcomes" value={crmData.outcomes || ''} onChange={handleInputChange} rows="2" className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Result of the meeting..."></textarea>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Follow-Up Actions</label>
            <input type="text" name="followUpActions" value={crmData.followUpActions || ''} onChange={handleInputChange} className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Tasks to do next" />
          </div>

          <div className="mt-8 bg-blue-50 rounded-xl p-6 border border-blue-100 shadow-sm">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">AI Suggested Follow-ups</h3>
            {crmData.suggestedFollowUps && crmData.suggestedFollowUps.length > 0 ? (
              <ul className="space-y-3">
                {crmData.suggestedFollowUps.map((item, index) => (
                  <li key={index} className="flex items-start bg-white p-3 rounded-lg shadow-sm border border-blue-100">
                    <span className="flex-shrink-0 h-5 w-5 text-blue-600 mt-0.5 mr-3">
                      <svg fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path></svg>
                    </span>
                    <span className="text-blue-900 font-medium">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-blue-700/80 italic">No suggestions yet. Chat with the AI to generate follow-ups.</p>
            )}
          </div>
        </form>
      </div>

      {/* Right Column: AI Assistant Chat */}
      <div className="w-1/2 flex flex-col h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200 p-6 flex items-center justify-between shadow-sm z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-800">AI Assistant</h2>
            <p className="text-sm text-gray-500 mt-1">Natural language CRM data entry</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full border border-green-100">Online</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {chatMessages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-8">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Welcome to your AI Assistant</h3>
              <p className="text-gray-500 max-w-sm">Try saying "I just met with Dr. Smith. We discussed the new clinical trial and he was very positive."</p>
            </div>
          ) : (
            chatMessages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'}`}>
                  <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 text-gray-500 rounded-2xl rounded-tl-sm p-4 shadow-sm flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 bg-white border-t border-gray-200">
          <form onSubmit={handleSendMessage} className="relative">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Type your message here..."
              className="w-full pl-5 pr-14 py-4 bg-gray-50 border border-gray-200 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-700 shadow-inner"
            />
            <button
              type="submit"
              disabled={loading || !inputText.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:hover:bg-blue-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
            </button>
          </form>
          <div className="mt-3 text-center">
            <span className="text-xs text-gray-400">Powered by LangGraph Agentic Workflow</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
