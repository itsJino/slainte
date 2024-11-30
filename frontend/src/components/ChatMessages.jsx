import Markdown from 'react-markdown';
import useAutoScroll from '@/hooks/useAutoScroll';
import Spinner from '@/components/Spinner';
import errorIcon from '@/assets/images/error.svg';
import HSELogo from '@/assets/images/hse_logo_green.png';

function ChatMessages({ messages, isLoading }) {
  const scrollContentRef = useAutoScroll(isLoading);

  return (
    <div className="bg-white p-4 rounded-xl">
      <div ref={scrollContentRef} className="grow space-y-4">
        {messages.map(({ role, content, loading, error }, idx) => (
          <div
            key={idx}
            className={`flex items-end gap-4 ${
              role === 'user' ? 'justify-end' : ''
            }`}
          >
            {role === 'assistant' && (
              <img
                className="h-[40px] w-[40px] shrink-0"
                src={HSELogo}
                alt="HSE logo"
              />
            )}
            <div
              className={`py-4 px-3 rounded-xl ${
                role === 'user'
                  ? 'bg-[#f3f3f3] text-black max-w-[50%] ml-auto'
                  : 'bg-[#006354] text-white max-w-[80%]'
              }`}
              style={{ width: 'fit-content' }}
            >
              <div>
                <div className="markdown-container">
                  {(loading && !content) ? <Spinner />
                    : (role === 'assistant')
                      ? <Markdown>{content}</Markdown>
                      : <div className="whitespace-pre-line">{content}</div>
                  }
                </div>
                {error && (
                  <div
                    className={`flex items-center gap-1 text-sm text-error-red ${
                      content && 'mt-2'
                    }`}
                  >
                    <img className="h-5 w-5" src={errorIcon} alt="error" />
                    <span>Error generating the response</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ChatMessages;
