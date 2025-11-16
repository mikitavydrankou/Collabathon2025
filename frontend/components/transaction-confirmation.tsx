'use client'

import { useState } from 'react'
import { ArrowLeft, CheckCircle2, Loader2, AlertCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface TransactionConfirmationProps {
	onBack: () => void
	onConfirm: () => void
	accountNumber: string
	recipientName: string
	amount: string
	title: string
	userId: number
}

export default function TransactionConfirmation({
	onBack,
	onConfirm,
	accountNumber,
	recipientName,
	amount,
	title,
	userId,
}: TransactionConfirmationProps) {
	const [isProcessing, setIsProcessing] = useState(false)
	const [isSuccess, setIsSuccess] = useState(false)
	const [error, setError] = useState<string | null>(null)

	const formatAmount = (value: string) => {
		const num = parseFloat(value)
		return new Intl.NumberFormat('pl-PL', {
			style: 'currency',
			currency: 'PLN',
			minimumFractionDigits: 2,
		}).format(num)
	}

	const handleCancel = () => {
		if (isProcessing) return // Prevent cancel during processing
		onBack()
	}

	const handleConfirm = async () => {
		setIsProcessing(true)
		setError(null)

		try {
			// Split recipient name into first and last name
			const nameParts = recipientName
				.trim()
				.split(/\s+/)
				.filter(part => part.length > 0)
			const receiver_name = (nameParts[0] || '').trim()
			const receiver_surname =
				nameParts.length > 1 ? nameParts.slice(1).join(' ').trim() : ''

			console.log('👤 Name parsing debug:')
			console.log('  - Original recipientName:', recipientName)
			console.log('  - After trim:', recipientName.trim())
			console.log('  - Name parts:', nameParts)
			console.log('  - receiver_name:', receiver_name)
			console.log('  - receiver_surname:', receiver_surname)

			// Validate that we have both name and surname
			if (!receiver_name || !receiver_surname) {
				throw new Error('Please enter both first name and last name')
			}

			// Clean account number (remove spaces)
			const cleanAccountNumber = accountNumber.replace(/\s+/g, '')

			// Parse amount (remove any formatting like spaces, commas)
			const cleanAmount = amount.replace(/[^\d.-]/g, '')
			const parsedAmount = parseFloat(cleanAmount)

			// Validate parsed amount
			if (isNaN(parsedAmount) || parsedAmount <= 0) {
				throw new Error('Invalid amount')
			}

			const requestBody = {
				user_id: userId,
				receiver_bank_number: cleanAccountNumber,
				receiver_name: receiver_name,
				receiver_surname: receiver_surname,
				amount: parsedAmount,
				transaction_text: title || `Transfer to ${recipientName}`,
			}

			console.log('🚀 Sending transaction request:', requestBody)

			// Call the real API
			const response = await fetch(
				'http://localhost:8000/transactions/create',
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify(requestBody),
				}
			)

			console.log(
				'📡 Response status:',
				response.status,
				response.statusText
			)

			const data = await response.json()
			console.log('📦 Response data:', data)

			if (!response.ok) {
				throw new Error(
					data.message ||
						`HTTP ${response.status}: ${response.statusText}`
				)
			}

			if (!data.success) {
				throw new Error(data.message || 'Transaction failed')
			}

			setIsSuccess(true)

			// Wait a bit before calling onConfirm
			setTimeout(() => {
				onConfirm()
			}, 1500)
		} catch (err) {
			console.error('❌ Transaction error:', err)
			setError(
				err instanceof Error
					? err.message
					: 'Transaction failed. Please try again.'
			)
			setIsProcessing(false)
		}
	}

	if (isSuccess) {
		return (
			<div className='min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col items-center justify-center p-4'>
				<div className='max-w-md w-full text-center space-y-6'>
					<div className='flex justify-center'>
						<div className='w-20 h-20 bg-green-500 rounded-full flex items-center justify-center animate-scale-in'>
							<CheckCircle2 className='w-12 h-12 text-white' />
						</div>
					</div>

					<div className='space-y-2'>
						<h2 className='text-2xl font-bold text-slate-900'>
							Transaction Successful!
						</h2>
						<p className='text-slate-600'>
							Your payment has been processed successfully
						</p>
					</div>

					<Card className='bg-white border-slate-200'>
						<CardContent className='p-6'>
							<div className='text-4xl font-bold text-slate-900 mb-1'>
								{formatAmount(amount)}
							</div>
							<div className='text-sm text-slate-600'>
								sent to {recipientName}
							</div>
						</CardContent>
					</Card>
				</div>
			</div>
		)
	}

	return (
		<div className='min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col'>
			{/* Header */}
			<div className='sticky top-0 bg-white border-b border-slate-200 px-4 py-4 z-10'>
				<div className='flex items-center gap-3 max-w-md mx-auto'>
					<button
						onClick={onBack}
						disabled={isProcessing}
						className='p-2 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50'
					>
						<ArrowLeft className='w-5 h-5 text-slate-900' />
					</button>
					<h1 className='text-lg font-semibold text-slate-900'>
						Confirm Transaction
					</h1>
				</div>
			</div>

			{/* Content */}
			<div className='flex-1 overflow-y-auto p-4'>
				<div className='max-w-md mx-auto space-y-6'>
					{/* Amount Card */}
					<Card className='bg-gradient-to-br from-yellow-400 to-yellow-500 border-0 shadow-lg'>
						<CardContent className='p-6 text-center'>
							<p className='text-sm text-slate-900 opacity-90 mb-2'>
								You are sending
							</p>
							<div className='text-5xl font-bold text-slate-900 mb-4'>
								{formatAmount(amount)}
							</div>
						</CardContent>
					</Card>

					{/* Transaction Details */}
					<Card className='bg-white border-slate-200'>
						<CardContent className='p-6 space-y-4'>
							<h3 className='text-sm font-semibold text-slate-900 mb-4'>
								Transaction Details
							</h3>

							{/* Recipient Name */}
							<div className='space-y-1'>
								<p className='text-xs text-slate-500 uppercase tracking-wide'>
									Recipient
								</p>
								<p className='text-base font-semibold text-slate-900'>
									{recipientName}
								</p>
							</div>

							<div className='border-t border-slate-100' />

							{/* Account Number */}
							<div className='space-y-1'>
								<p className='text-xs text-slate-500 uppercase tracking-wide'>
									Account Number
								</p>
								<p className='text-base font-mono text-slate-900 break-all'>
									{accountNumber}
								</p>
							</div>

							<div className='border-t border-slate-100' />

							{/* Transfer Title */}
							<div className='space-y-1'>
								<p className='text-xs text-slate-500 uppercase tracking-wide'>
									Transfer Title
								</p>
								<p className='text-base text-slate-900'>
									{title}
								</p>
							</div>

							<div className='border-t border-slate-100' />

							{/* Amount Breakdown */}
							<div className='space-y-2 pt-2'>
								<div className='flex justify-between items-center'>
									<span className='text-sm text-slate-600'>
										Amount
									</span>
									<span className='text-sm font-medium text-slate-900'>
										{formatAmount(amount)}
									</span>
								</div>
								<div className='flex justify-between items-center'>
									<span className='text-sm text-slate-600'>
										Fee
									</span>
									<span className='text-sm font-medium text-slate-900'>
										0.00 zł
									</span>
								</div>
								<div className='border-t border-slate-200 pt-2 mt-2'>
									<div className='flex justify-between items-center'>
										<span className='text-base font-semibold text-slate-900'>
											Total
										</span>
										<span className='text-base font-bold text-slate-900'>
											{formatAmount(amount)}
										</span>
									</div>
								</div>
							</div>
						</CardContent>
					</Card>

					{/* Security Notice */}
					<div className='flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg'>
						<AlertCircle className='w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5' />
						<div className='flex-1'>
							<p className='text-sm text-blue-900'>
								Please review all details carefully before
								confirming. This transaction cannot be undone.
							</p>
						</div>
					</div>

					{/* Error Message */}
					{error && (
						<div className='flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg'>
							<AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
							<div className='flex-1'>
								<p className='text-sm text-red-900'>{error}</p>
							</div>
						</div>
					)}
				</div>
			</div>

			{/* Bottom Action */}
			<div className='sticky bottom-0 bg-white border-t border-slate-200 p-4'>
				<div className='max-w-md mx-auto space-y-3'>
					<Button
						onClick={handleConfirm}
						disabled={isProcessing}
						className='w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold py-6 text-base disabled:opacity-50'
					>
						{isProcessing ? (
							<>
								<Loader2 className='w-5 h-5 mr-2 animate-spin' />
								Processing...
							</>
						) : (
							<>
								<CheckCircle2 className='w-5 h-5 mr-2' />
								Confirm & Send
							</>
						)}
					</Button>

					<Button
						onClick={handleCancel}
						disabled={isProcessing}
						variant='outline'
						className='w-full border-slate-300 text-slate-700 hover:bg-slate-50 font-medium py-3 disabled:opacity-50'
					>
						<X className='w-4 h-4 mr-2' />
						Cancel Transaction
					</Button>

					<p className='text-xs text-center text-slate-500'>
						By confirming, you agree to the transaction terms
					</p>
				</div>
			</div>

			<style jsx>{`
				@keyframes scale-in {
					0% {
						transform: scale(0);
						opacity: 0;
					}
					50% {
						transform: scale(1.1);
					}
					100% {
						transform: scale(1);
						opacity: 1;
					}
				}
				.animate-scale-in {
					animation: scale-in 0.5s ease-out;
				}
			`}</style>
		</div>
	)
}
