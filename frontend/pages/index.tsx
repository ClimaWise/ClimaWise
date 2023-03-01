import { Layout, Text, Page } from '@vercel/examples-ui'
import { Chat } from '../components/Chat'

function Home() {
  return (
    <div id="root" className="bg-gray-900 flex items-center justify-center w-screen h-screen flex-col">
      <section className="flex flex-col gap-6">
        <h1 className=" text-white text-3xl font-bold flex items-center justify-center ">ClimaWise</h1>
        {/* <span className="text-zinc-600">
          An intelligent chat assistant for climate policy questions.
        </span> */}
      </section>

      <section className="flex flex-col gap-3 items-center justify-center w-screen h-5/6 ">
        {/* <h2 >Chat:</h2> */}
        <div className="lg:w-2/3 no-scrollbar overflow-y-scroll h-full ">
          <Chat />
        </div>
      </section>
    </div> 
  )
}

// Home.Layout = Layout

export default Home
