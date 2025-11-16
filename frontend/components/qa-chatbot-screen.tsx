'use client'

import { useState, useEffect, useRef } from 'react'
import { ArrowLeft, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'

interface QAChatbotScreenProps {
	onBack: () => void
	onSelectTransferOption?: (option: string) => void
	initialMessage?: string
}

interface ChatMessage {
	id: string
	role: 'user' | 'assistant'
	content: string
	tools_used?: string[]
	timestamp: string
}

export default function QAChatbotScreen({
	onBack,
	onSelectTransferOption,
	initialMessage,
}: QAChatbotScreenProps) {
	const [messages, setMessages] = useState<ChatMessage[]>([
		{
			id: 'welcome',
			role: 'assistant',
			content:
				"Hello. I'm your banking assistant.\n\nI can help you with:\n\n• Check your balance\n• View recent transactions\n• Search transaction history\n• Find similar transactions\n\nWhat would you like to know?",
			timestamp: new Date().toISOString(),
		},
	])
	const [inputValue, setInputValue] = useState('')
	const [sessionId, setSessionId] = useState<string | null>(null)
	const [isLoading, setIsLoading] = useState(false)
	const messagesEndRef = useRef<HTMLDivElement>(null)

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
	}

	// Convert markdown bold (**text**) to HTML
	const renderMarkdown = (text: string): string => {
		// Escape HTML to prevent XSS
		const escaped = text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')

		// Convert markdown bold to HTML with dark color
		const withBold = escaped.replace(
			/\*\*(.*?)\*\*/g,
			'<strong class="text-slate-900 font-semibold">$1</strong>'
		)

		// Convert newlines to <br />
		return withBold.replace(/\n/g, '<br />')
	}

	useEffect(() => {
		scrollToBottom()
	}, [messages])

	const addMessage = (message: ChatMessage) => {
		setMessages(prev => [...prev, message])
	}

	const sendMessage = async (messageText: string) => {
		if (!messageText.trim()) return

		const userMessage = messageText.trim()

		// Add user message
		addMessage({
			id: `user-${Date.now()}`,
			role: 'user',
			content: userMessage,
			timestamp: new Date().toISOString(),
		})

		setIsLoading(true)
		try {
			const response = await apiClient.sendQAMessage({
				message: userMessage,
				session_id: sessionId || undefined,
			})

			// Update session ID if it's the first message
			if (!sessionId) {
				setSessionId(response.session_id)
			}

			// Add assistant response
			addMessage({
				id: `assistant-${Date.now()}`,
				role: 'assistant',
				content: response.message,
				tools_used: response.tools_used,
				timestamp: new Date().toISOString(),
			})
		} catch (error: any) {
			addMessage({
				id: `error-${Date.now()}`,
				role: 'assistant',
				content: `❌ Error: ${error.message}`,
				timestamp: new Date().toISOString(),
			})
		} finally {
			setIsLoading(false)
		}
	}

	const handleSendMessage = async () => {
		if (!inputValue.trim()) return
		const message = inputValue.trim()
		setInputValue('')
		await sendMessage(message)
	}

	// Auto-send initial message if provided
	const sentInitialMessage = useRef<string | null>(null)
	useEffect(() => {
		if (
			initialMessage &&
			initialMessage.trim() &&
			sentInitialMessage.current !== initialMessage
		) {
			sentInitialMessage.current = initialMessage
			sendMessage(initialMessage)
		}
		// Reset when initialMessage is cleared
		if (!initialMessage) {
			sentInitialMessage.current = null
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [initialMessage])

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault()
			handleSendMessage()
		}
	}

	return (
		<div className='min-h-screen flex flex-col bg-slate-50'>
			{/* Header */}
			<div className='bg-slate-900 text-white px-4 py-4 shadow-lg border-t border-slate-800'>
				<div className='flex items-center gap-3 max-w-md mx-auto'>
					<button
						onClick={onBack}
						aria-label='Go back to dashboard'
						className='p-2 hover:bg-slate-800 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-700 focus:ring-offset-2 focus:ring-offset-slate-900'
					>
						<ArrowLeft
							size={24}
							aria-hidden='true'
							className='text-white'
						/>
						<span className='sr-only'>Back</span>
					</button>
					<div className='flex-1'>
						<h1 className='text-xl font-bold text-white'>
							Q&A Assistant
						</h1>
						<p className='text-sm text-slate-300'>
							Ask about your transactions
						</p>
					</div>
				</div>
			</div>

			{/* Messages */}
			<div
				className='flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-md mx-auto w-full'
				role='log'
				aria-live='polite'
				aria-label='Chat messages'
			>
				{messages.map(msg => (
					<div key={msg.id}>
						<div
							className={`flex ${
								msg.role === 'user'
									? 'justify-end'
									: 'justify-start'
							}`}
						>
							<div
								className={`max-w-[85%] rounded-2xl px-4 py-3 ${
									msg.role === 'user'
										? 'bg-yellow-400 text-slate-900'
										: 'bg-white text-slate-900 shadow-md border border-slate-200'
								}`}
								role={
									msg.role === 'assistant'
										? 'status'
										: undefined
								}
								aria-live={
									msg.role === 'assistant'
										? 'polite'
										: undefined
								}
							>
								<p
									className='text-sm whitespace-pre-line leading-relaxed'
									dangerouslySetInnerHTML={{
										__html: renderMarkdown(msg.content),
									}}
								/>
							</div>
						</div>
					</div>
				))}

				{isLoading && (
					<div className='flex justify-start'>
						<div className='bg-white rounded-2xl px-4 py-3 shadow-md border border-slate-200'>
							<div className='flex gap-1'>
								<div className='w-2 h-2 bg-yellow-400 rounded-full animate-bounce'></div>
								<div
									className='w-2 h-2 bg-yellow-400 rounded-full animate-bounce'
									style={{ animationDelay: '0.1s' }}
								></div>
								<div
									className='w-2 h-2 bg-yellow-400 rounded-full animate-bounce'
									style={{ animationDelay: '0.2s' }}
								></div>
							</div>
						</div>
					</div>
				)}

				<div ref={messagesEndRef} />
			</div>

			{/* Input area */}
			<div className='bg-white border-t border-slate-200 px-4 py-4'>
				<div className='flex gap-2 max-w-md mx-auto'>
					<input
						type='text'
						value={inputValue}
						onChange={e => setInputValue(e.target.value)}
						onKeyPress={handleKeyPress}
						placeholder='Ask about your transactions...'
						disabled={isLoading}
						aria-label='Type your question about transactions'
						aria-describedby='input-help'
						className='flex-1 px-4 py-3 border-2 border-slate-300 rounded-full focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-200 transition-all text-slate-900 placeholder:text-slate-400 disabled:bg-slate-100 text-base'
					/>
					<span id='input-help' className='sr-only'>
						Type your question and press Enter or click Send
					</span>
					<button
						onClick={handleSendMessage}
						disabled={!inputValue.trim() || isLoading}
						aria-label='Send message'
						aria-disabled={!inputValue.trim() || isLoading}
						className='bg-yellow-400 hover:bg-yellow-500 text-slate-900 rounded-full p-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md focus:outline-none focus:ring-2 focus:ring-yellow-200 focus:ring-offset-2'
					>
						<Send size={20} aria-hidden='true' />
						<span className='sr-only'>Send</span>
					</button>
				</div>
			</div>
		</div>
	)
}
