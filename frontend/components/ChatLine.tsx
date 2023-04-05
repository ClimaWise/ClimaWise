import clsx from 'clsx'
import Balancer from 'react-wrap-balancer'

/* NOTE FOR DEBUGGING: print statements in this file are typically best viewing the browser console.*/

// wrap Balancer to remove type errors :( - @TODO - fix this ugly hack
const BalancerWrapper = (props: any) => <Balancer {...props} />

export type Message = {
  who: 'bot' | 'user' | undefined
  message?: [string]
  url?: [[string]]
  references?: [number]
}

// loading placeholder animation for the chat line
export const LoadingChatLine = () => (
  <div className="flex min-w-full animate-pulse px-4 py-5 sm:px-6">
    <div className="flex flex-grow space-x-3">
      <div className="min-w-0 flex-1">
        <p className="font-large text-xxl text-gray-900">
          <a href="#" className="hover:underline">
            ClimaWise
          </a>
        </p>
        <div className="space-y-4 pt-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 h-2 rounded bg-zinc-500"></div>
            <div className="col-span-1 h-2 rounded bg-zinc-500"></div>
          </div>
          <div className="h-2 rounded bg-zinc-500"></div>
        </div>
      </div>
    </div>
  </div>
)

// util helper to convert new lines to <br /> tags
const convertNewLines = (text: [string], urls?: [[string]], references?: [[number]]) => {
  if (!urls || !references) {

    return (
      text[0].split('\n').map((line, i) => (
        <span key={i}>
          {line}
          <br />
        </span>
      ))
    )
  } else {

    let sentenceJsx;
    let textblock = []
    let logos = []
    let usedLogos = [String]

    for (let i = 0; i < text.length; i++) {

      const sentence = text[i]
      const ref = references[i]

      if (!ref || !text) {
        sentenceJsx = (<div className='flex flex-col'><span key={i}>
          {sentence}
          <br />
        </span>

        </div>
        )
        textblock.push(sentenceJsx)
        continue
      }
      // TODO iterate over urls uring ref to get urls and logos
      let links = []

      for (let j = 0; j < ref.length; j++) {
        let refNum = ref[j]

        let link = urls[refNum][0]

        let logo;
        if (urls[refNum].length > 1) {
          logo = urls[refNum][1]
          if (!usedLogos.includes(logo)) {

            logos.push(
              <a href={link} key={refNum} className=" hover:text-gray-700 ">
                <img className='block w-[24px] h-[24px]' src={logo} alt="self.com favicon" width="20" height="20"></img>
              </a>
            )
            usedLogos.push(logo)
          }
        }

        if (links.length > 0) {
          links.push(', ')
          links.push((<p>&nbsp;</p>))
        }
        links.push(<a href={link} key={refNum} className=" hover:text-gray-700 ">
          {refNum}
        </a>)

      }

      sentenceJsx = (
        <span key={i} className="flex">
          {sentence} <div className="flex justify-center items-start mb-5 text-gray-400 hover:cursor-pointer text-xs"> . &nbsp;[{links}] </div>
          <br />
        </span>
      )
      textblock.push(sentenceJsx)
    }

    if (logos.length) {
      textblock.push(<div className="w-full border-t-2 mb-10 mt-10"></div>
      )

      textblock.push(<ul id="logos" className="flex justify-between items-end mb-10">
        {logos}
      </ul>)
    }
    return (textblock)
  }

}
// text.split('\n').map((line, i) => (
//   <span key={i}>
//     {line}
//     <br />
//   </span>
// ))

export function ChatLine({ who = 'bot', message, url, references }: Message) {
  if (!message) {
    return null
  }

  const formatteMessage = convertNewLines(message, url, references)
  // const formatteMessage = convertNewLines(url)

  return (
    <div
      className={
        who != 'bot' ? 'float-right clear-both' : 'float-left clear-both'
      }
    >
      <BalancerWrapper>
        <div className="float-right mb-5 rounded-lg bg-white px-4 py-5 shadow-lg ring-1 ring-zinc-100 sm:px-6">
          <div className="flex space-x-3">
            <div className="flex-1 gap-4">
              <p className="font-large text-xxl text-gray-900">
                <a href="#" className="hover:underline">
                  {who == 'bot' ? 'ClimaWise' : 'You'}
                </a>
              </p>
              {/* {url && (
                <p className="text">
         
                </p>
              )} */}
              {formatteMessage}

            </div>
          </div>
        </div>
      </BalancerWrapper>
    </div>
  )
}
