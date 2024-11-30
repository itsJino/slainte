import Chatbot from '@/components/Chatbot';
import HSELogo from '@/assets/images/hse_logo_green.png';

function App() {

  return (
    <div className='flex flex-col min-h-full w-full max-w-3xl mx-auto px-4'>
      <header className='sticky top-0 shrink-0 z-20 bg-white'>
        <div className='flex flex-col h-full w-full gap-1 pt-4 pb-2'>
          <img src={HSELogo} alt='logo' className='w-20 h-20 mx-auto' />
          <h1 className='font-urbanist text-[1.65rem] font-semibold'>Slainte</h1>
        </div>
      </header>
      <Chatbot />
    </div>
  );
}

export default App;