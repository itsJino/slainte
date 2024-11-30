import React, { useCallback } from 'react';
import useAutosize from '@/hooks/useAutosize';
import sendIcon from '@/assets/images/send.svg';

function ChatInput({ newMessage, isLoading, setNewMessage, submitNewMessage }) {
  const textareaRef = useAutosize(newMessage);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      if (newMessage.trim()) {
        submitNewMessage();
      }
    }
  }, [newMessage, isLoading, submitNewMessage]);

  const handleChange = useCallback((e) => {
    setNewMessage(e.target.value);
  }, [setNewMessage]);

  const isSendDisabled = isLoading || !newMessage.trim();

  return (
    <div className="sticky bottom-0 py-4 z-50">
      <div className="p-1.5 rounded-3xl font-mono origin-bottom animate-chat duration-400">
        <div
          className={`relative shrink-0 rounded-3xl overflow-hidden ring-[#006354] ring-1 
            focus-within:ring-2 transition-all ${
              isLoading ? 'opacity-50 pointer-events-none' : ''
            }`}
        >
          <textarea
            className="block w-full max-h-[140px] py-2 px-4 pr-11 rounded-3xl resize-none 
              placeholder:text-[#006354] placeholder:leading-4 placeholder:-translate-y-1 
              sm:placeholder:leading-normal sm:placeholder:translate-y-0 focus:outline-none focus:ring-0"
            ref={textareaRef}
            rows="1"
            value={newMessage}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            aria-label="Chat input"
            disabled={isLoading}
          />
          <button
            className={`absolute top-1/2 -translate-y-1/2 right-3 p-1 rounded-md 
              ${
                isSendDisabled
                  ? 'cursor-not-allowed'
                  : ''
              } transition-all`}
            onClick={() => {
              if (!isSendDisabled) {
                submitNewMessage();
              }
            }}
            aria-label="Send message"
            disabled={isSendDisabled}
          >
            <img src={sendIcon} alt="Send" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default React.memo(ChatInput);
