'use client'

import { MessageSquare, ZapOff, HelpCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TransferOptionsPopupProps {
	onClose: () => void
	onSelectOption: (option: string) => void
}

export default function TransferOptionsPopup({
	onClose,
	onSelectOption,
}: TransferOptionsPopupProps) {
	const handleOptionSelect = (option: string) => {
		onSelectOption(option)
		onClose()
	}

	return (
		<>
			{/* Backdrop */}
			<div className='fixed inset-0 bg-black/40 z-40' onClick={onClose} />

			{/* Popup Container */}
			<div className='fixed inset-x-0 top-20 max-w-md mx-auto z-50'>
				<div className='mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2'>
					<div className='flex items-start justify-between mb-4'>
						<div>
							<h3 className='font-semibold text-slate-900 mb-2'>
								Choose Transfer Support
							</h3>
							<p className='text-sm text-slate-600'>
								Select how much help you need with your
								transfer:
							</p>
						</div>
						<button
							onClick={onClose}
							className='p-1 hover:bg-slate-100 rounded-lg transition-colors'
						>
							<X className='w-5 h-5 text-slate-400' />
						</button>
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
						Cancel
					</Button>
				</div>
			</div>
		</>
	)
}
