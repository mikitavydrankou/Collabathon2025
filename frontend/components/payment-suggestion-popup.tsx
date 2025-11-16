'use client'

import { X, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PaymentSuggestionPopupProps {
	onClose: () => void
	onShowMe: () => void
	recipientName?: string
	amount?: string
}

export default function PaymentSuggestionPopup({
	onClose,
	onShowMe,
	recipientName = 'Mike Wilson',
	amount = '1,500.00 zł',
}: PaymentSuggestionPopupProps) {
	return (
		<>
			{/* Backdrop */}
			<div className='fixed inset-0 bg-black/40 z-40' onClick={onClose} />

			{/* Popup Container */}
			<div className='fixed inset-x-0 top-20 max-w-md mx-auto z-50'>
				<div className='mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2'>
					<div className='flex items-start justify-between mb-4'>
						<div className='flex items-center gap-3'>
							<div className='w-10 h-10 rounded-full bg-green-100 flex items-center justify-center'>
								<TrendingUp className='w-5 h-5 text-green-600' />
							</div>
							<div>
								<h3 className='font-semibold text-slate-900'>
									Recurring Payment Detected
								</h3>
								<p className='text-xs text-slate-500'>
									Payment Pattern
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

					<p className='text-sm text-slate-700 mb-6'>
						The last 3 months you have made a payment at this time to{' '}
						<span className='font-semibold text-slate-900'>
							{recipientName}
						</span>
						, would you like to do this again?
					</p>

					<div className='flex gap-3'>
						<Button
							onClick={onClose}
							variant='outline'
							className='flex-1 border-slate-300 text-slate-700 hover:bg-slate-50'
						>
							Not now
						</Button>
						<Button
							onClick={onShowMe}
							className='flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold'
						>
							Show me
						</Button>
					</div>

					<p className='text-xs text-slate-500 text-center mt-3'>
						"Show me" will open transfer options for this payment
					</p>
				</div>
			</div>
		</>
	)
}

