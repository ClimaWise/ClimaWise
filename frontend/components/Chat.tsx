import { useEffect, useState } from 'react'
import { Button } from './Button'
import { type Message, ChatLine, LoadingChatLine } from './ChatLine'
import { useCookies } from 'react-cookie'

/* NOTE FOR DEBUGGING: print statements in this file are typically best viewing the browser console.*/

const COOKIE_NAME = 'nextjs-example-ai-chat-gpt3'

// default first message to display in UI (not necessary to define the prompt)
export const initialMessages: Message[] = [
  {
    who: 'bot',
    // message: 'This is ClimaWise. Ask me anything relating to Climate Policy.',
    message: ['This is ClimaWise. Ask me anything relating to Climate Policy.'],

  },
]

const InputMessage = ({ input, setInput, sendMessage }: any) => (
  <div className=" mt-6 flex clear-both h-fit	w-fit " id="input-and-button-holder">
    <div id="float-holder"
      className="flex fixed bottom-5 left-1/2 transform -translate-x-1/2 h-20 w-auto max-w-5xl right-0 bg-zinc-800 outline-none focus:outline-none rounded-full pr-8 py-sm border text-zinc-800 border-zinc-300 focus:ring-2 focus:ring-zinc-900 focus:border-zinc-400 dark:bg-darkOffsetPlus dark:text-zinc-300 dark:placeholder-zinc-500 dark:focus:bg-zinc-900 dark:border-zinc-600 dark:focus:border-zinc-800 dark:focus:ring-zinc-800 font-sans font-medium transition-all duration-300 ease-in-out md:text-lg">
      <Button
        id="ask-button"
        type="submit"

        className="rounded-l-full h-full w-64 "

        onClick={() => {
          // User-defined messages.
          sendMessage([input])
          setInput('')
        }}
      >
        ask
      </Button>

      <input
        // type="text"
        aria-label="chat input"
        required
        type="search" placeholder="Ask a follow up"
        id="question-field"

        className="pl-10 bg-transparent	clear-both h-full w-full outline-none focus:outline-none text-white font-sans font-medium transition-all md:text-lg"

        value={input}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            sendMessage(input)
            setInput('')
          }
        }}
        onChange={(e) => {
          setInput(e.target.value)
        }}
      />
    </div>
  </div>
)

export function Chat() {


  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [cookie, setCookie] = useCookies([COOKIE_NAME])

  useEffect(() => {
    if (!cookie[COOKIE_NAME]) {
      // generate a semi random short id
      const randomId = Math.random().toString(36).substring(7)
      setCookie(COOKIE_NAME, randomId)
    }
  }, [cookie, setCookie])

  // send message to API /api/chat endpoint
  const sendMessage = async (message: [string]) => {
    setLoading(true)
    const newMessages = [
      ...messages,
      { message: message, who: 'user' } as Message,
    ]
    setMessages(newMessages)
    const last10messages = newMessages.slice(-10)

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: last10messages,
        user: cookie[COOKIE_NAME],
      }),
    })
    const data = await response.json()


    // strip out white spaces from the bot message
    // const botNewMessage = data.text.trim()
    // const botNewUrl = data.url.trim()
    // const botNewImage = data.image.trim()
    // TODO: trim all the input data if necessary (see above, as was done before transfer to lists)
    const botNewMessage = data.textList
    const botNewUrl = data.urlList
    const botNewReferences = data.referenceList


    setMessages([
      ...newMessages,
      { message: botNewMessage, url: botNewUrl, references: botNewReferences, who: 'bot' } as Message,
    ])


    setLoading(false)
  }

  return (
    <div className="rounded-2xl border-zinc-100  lg:border lg:p-6 h-full no-scrollbar overflow-y-scroll h-full" id="chatbox">
      {messages.map(({ message, who, url, references }, index) => (
        <ChatLine key={index} who={who} message={message} url={url} references={references} />
      ))}

      {loading && <LoadingChatLine />}

      {messages.length < 2 && (
        <span className="mx-auto flex flex-grow text-gray-600 clear-both">
          Type a message to start the conversation
        </span>
      )}
      <InputMessage
        input={input}
        setInput={setInput}
        sendMessage={sendMessage}
      // 
      />
    </div>
  )
}
