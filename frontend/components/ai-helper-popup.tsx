'use client'

import { useState } from 'react'
import {
	MessageCircle,
	X,
	Send,
	MessageSquare,
	ZapOff,
	HelpCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AIHelperPopupProps {
	onClose: () => void
	onSelectOption?: (option: string) => void
	onSendToQA?: (message: string) => void
}

export default function AIHelperPopup({
	onClose,
	onSelectOption,
	onSendToQA,
}: AIHelperPopupProps) {
	const [step, setStep] = useState<'popup' | 'input' | 'options'>('popup')
	const [message, setMessage] = useState('')

	const handleAccept = () => {
		setStep('input')
	}

	const handleSendMessage = () => {
		if (message.trim() && onSendToQA) {
			onSendToQA(message)
			onClose()
		}
	}

	const handleShowTransferOptions = () => {
		setStep('options')
	}

	const handleOptionSelect = (option: string) => {
		onSelectOption?.(option)
		onClose()
	}

	return (
		<>
			{/* Backdrop */}
			<div className='fixed inset-0 bg-black/40 z-40' onClick={onClose} />

			{/* Popup Container */}
			<div className='fixed inset-x-0 top-20 max-w-md mx-auto z-50'>
				{step === 'popup' && (
					<div className='mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2'>
						<div className='flex items-start justify-between mb-4'>
							<div className='flex items-center gap-3'>
								<div className='w-10 h-10 rounded-full bg-yellow-400 flex items-center justify-center'>
									<MessageCircle className='w-5 h-5 text-slate-900' />
								</div>
								<div>
									<h3 className='font-semibold text-slate-900'>
										Do you need help?
									</h3>
									<p className='text-xs text-slate-500'>
										AI Assistant
									</p>
								</div>
							</div>
							<button
								onClick={onClose}
								className='p-1 hover:bg-slate-100 rounded-lg transition-colors'
							>
								<X className='w-5 h-5 text-slate-400' />
							</button>
						</div>
						<p className='text-sm text-slate-600 mb-6'>
							I can help you answer questions or guide you through
							transfers. What do you need?
						</p>
						<div className='space-y-2 mb-4'>
							<button
								onClick={() => handleOptionSelect('qa_chatbot')}
								className='w-full p-3 text-left bg-slate-50 hover:bg-yellow-50 rounded-lg transition-colors border border-slate-200 hover:border-yellow-400 flex items-center gap-3'
							>
								<HelpCircle className='w-5 h-5 text-yellow-400 flex-shrink-0' />
								<div>
									<p className='text-sm font-medium text-slate-900'>
										Ask Questions
									</p>
									<p className='text-xs text-slate-500'>
										About balance & transactions
									</p>
								</div>
							</button>
						</div>
						<div className='flex gap-3'>
							<Button
								onClick={onClose}
								variant='outline'
								className='flex-1 border-slate-300 text-slate-700 hover:bg-slate-50'
							>
								Not now
							</Button>
							<Button
								onClick={handleAccept}
								className='flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold'
							>
								More options
							</Button>
						</div>
					</div>
				)}

				{step === 'input' && (
					<div className='mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2'>
						<div className='flex items-center gap-2 mb-4'>
							<button
								onClick={() => setStep('popup')}
								className='p-1 hover:bg-slate-100 rounded-lg'
							>
								<X className='w-5 h-5 text-slate-400' />
							</button>
							<h3 className='font-semibold text-slate-900 flex-1'>
								Ask me anything
							</h3>
						</div>
						<div className='space-y-3'>
							<textarea
								value={message}
								onChange={e => setMessage(e.target.value)}
								placeholder='Type your question...'
								className='w-full p-3 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400 resize-none'
								rows={3}
							/>
							<Button
								onClick={handleShowTransferOptions}
								className='w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-semibold flex items-center justify-center gap-2'
							>
								<Send className='w-4 h-4' />
								Transfer Money
							</Button>
							<Button
								onClick={handleSendMessage}
								disabled={!message.trim()}
								className='w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed'
							>
								<Send className='w-4 h-4' />
								Send
							</Button>
						</div>
					</div>
				)}

<<<<<<< Updated upstream
				{step === 'options' && (
					<div className='mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2'>
						<div className='mb-4'>
							<h3 className='font-semibold text-slate-900 mb-2'>
								Choose Transfer Support
							</h3>
							<p className='text-sm text-slate-600'>
								How much help do you need with your transfer?
							</p>
						</div>
						<div className='space-y-2'>
							{[
								{
									label: 'Payment Assistant',
									action: 'chatbot',
									icon: MessageSquare,
									desc: 'AI guides you step-by-step',
								},
								{
									label: 'Full Support',
									action: 'full_support',
									icon: HelpCircle,
									desc: 'Complete step-by-step guide',
								},
								{
									label: 'Partial Support',
									action: 'partial_support',
									icon: HelpCircle,
									desc: 'Light hints and tips',
								},
								{
									label: 'No Support',
									action: 'no_support',
									icon: ZapOff,
									desc: 'Direct transfer form',
								},
							].map(option => {
								const Icon = option.icon
								return (
									<button
										key={option.action}
										onClick={() =>
											handleOptionSelect(option.action)
										}
										className='w-full p-3 text-left bg-slate-50 hover:bg-yellow-50 rounded-lg transition-colors border border-slate-200 hover:border-yellow-400 flex items-center gap-3'
									>
										<Icon className='w-5 h-5 text-yellow-400 flex-shrink-0' />
										<div>
											<p className='text-sm font-medium text-slate-900'>
												{option.label}
											</p>
											<p className='text-xs text-slate-500'>
												{option.desc}
											</p>
										</div>
									</button>
								)
							})}
						</div>
						<Button
							onClick={onClose}
							variant='outline'
							className='w-full mt-4 border-slate-300 text-slate-700'
						>
							Close
						</Button>
					</div>
				)}
			</div>
		</>
	)
=======
        {step === 'options' && (
          <div className="mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2">
            <div className="mb-4">
              <h3 className="font-semibold text-slate-900 mb-2">How can I help?</h3>
              <p className="text-sm text-slate-600">Choose your preferred support level:</p>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Chatbot', action: 'chatbot', icon: MessageSquare, desc: 'Chat with AI' },
                { label: 'Step by step explanations', action: 'full_support', icon: HelpCircle, desc: 'Step-by-step guide' },
                { label: 'Quality checks only', action: 'partial_support', icon: HelpCircle, desc: 'Light hints' },
                { label: 'Basic payment form', action: 'no_support', icon: ZapOff, desc: 'Just send money' },
              ].map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.action}
                    onClick={() => handleOptionSelect(option.action)}
                    className="w-full p-3 text-left bg-slate-50 hover:bg-yellow-50 rounded-lg transition-colors border border-slate-200 hover:border-yellow-400 flex items-center gap-3"
                  >
                    <Icon className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">{option.label}</p>
                      <p className="text-xs text-slate-500">{option.desc}</p>
                    </div>
                  </button>
                )
              })}
            </div>
            <Button
              onClick={onClose}
              variant="outline"
              className="w-full mt-4 border-slate-300 text-slate-700"
            >
              Close
            </Button>
          </div>
        )}
      </div>
    </>
  )
>>>>>>> Stashed changes
}
