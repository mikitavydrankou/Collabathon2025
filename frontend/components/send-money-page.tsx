"use client";

import { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  Send,
  ChevronRight,
  ArrowRight,
  AlertCircle,
  CreditCard,
  User,
  DollarSign,
  FileText,
  Target,
  Lightbulb,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import TransactionConfirmation from "./transaction-confirmation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SendMoneyPageProps {
  onBack: () => void;
  supportLevel?: "full" | "partial" | "none";
  userData?: {
    user_id: number;
    name: string;
    surname: string;
    email: string;
    balance: number;
    bank_number: string;
  };
  prefillData?: {
    accountNumber?: string;
    recipientName?: string;
    amount?: string;
    title?: string;
  } | null;
}

interface ValidationError {
  field: string;
  message: string;
  suggestion?: string;
  receiverName?: string;
  userInput?: string;
  errorPosition?: number;
}

export default function SendMoneyPage({
  onBack,
  supportLevel = "none",
  userData,
  prefillData,
}: SendMoneyPageProps) {
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showSimplePopup, setShowSimplePopup] = useState(false);
  const [showFullSupportPopup, setShowFullSupportPopup] = useState(false);

  const [accountNumber, setAccountNumber] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [amount, setAmount] = useState("");
  const [title, setTitle] = useState("");
  const [recipients, setRecipients] = useState<
    { user_id: number; name: string; surname: string; bank_number: string }[]
  >([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/users`)
      .then((r) => r.json())
      .then((data) => setRecipients(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] =
    useState<ValidationError | null>(null);
  const [hasSeenError, setHasSeenError] = useState(false);
  const [suggestedReceiverName, setSuggestedReceiverName] =
    useState<string>("");

  // Validation states for partial support mode
  const [accountNumberError, setAccountNumberError] =
    useState<ValidationError | null>(null);
  const [recipientNameError, setRecipientNameError] =
    useState<ValidationError | null>(null);
  const [amountError, setAmountError] = useState<ValidationError | null>(null);
  const [isValidatingPartial, setIsValidatingPartial] = useState<{
    accountNumber: boolean;
    recipientName: boolean;
    amount: boolean;
  }>({
    accountNumber: false,
    recipientName: false,
    amount: false,
  });
  const [showDraftRestored, setShowDraftRestored] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  const inputRef = useRef<HTMLInputElement | null>(null);

  // Get user ID from userData or fallback to 1
  const userId = userData?.user_id || 1;

  // Format IBAN with spaces after every 4 characters
  const formatIBAN = (value: string) => {
    // Remove all spaces and non-digit characters
    const cleaned = value.replace(/\s/g, "");
    // Add space after every 4 characters
    const formatted = cleaned.match(/.{1,4}/g)?.join(" ") || cleaned;
    return formatted;
  };

  // Restore draft from localStorage on mount or use prefillData
  useEffect(() => {
    // First check for prefillData (from reminder popup)
    if (prefillData) {
      if (prefillData.accountNumber)
        setAccountNumber(formatIBAN(prefillData.accountNumber));
      if (prefillData.recipientName) setRecipientName(prefillData.recipientName);
      if (prefillData.amount) setAmount(prefillData.amount);
      if (prefillData.title) setTitle(prefillData.title);
      return; // Don't check localStorage if we have prefillData
    }

    // Otherwise, check for draft in localStorage
    const draftStr = localStorage.getItem("transferDraft");
    if (draftStr) {
      try {
        const draft = JSON.parse(draftStr);
        if (draft.accountNumber)
          setAccountNumber(formatIBAN(draft.accountNumber));
        if (draft.recipientName) setRecipientName(draft.recipientName);
        if (draft.amount) setAmount(draft.amount);
        if (draft.title) setTitle(draft.title);

        // Restore current step in full support mode
        if (draft.currentStep !== undefined && supportLevel === "full") {
          setCurrentFieldIndex(draft.currentStep);
          console.log("📋 Restored to step:", draft.currentStep + 1);
        }

        // Show notification that draft was restored
        setShowDraftRestored(true);

        // Hide notification after 5 seconds
        setTimeout(() => {
          setShowDraftRestored(false);
        }, 5000);

        // Clear draft from localStorage after restoring
        localStorage.removeItem("transferDraft");
      } catch (e) {
        console.error("Failed to restore draft:", e);
      }
    }
  }, [supportLevel, prefillData]);

  const fields = [
    {
      name: "accountNumber",
      label: "Account Number",
      placeholder: "3389 3704 0044 0532",
      hint: "Enter the recipient IBAN",
      value: accountNumber,
      setValue: setAccountNumber,
    },
    {
      name: "name",
      label: "Recipient Name",
      placeholder: "Full name",
      hint: "Who are you sending to?",
      value: recipientName,
      setValue: setRecipientName,
    },
    {
      name: "amount",
      label: "Amount",
      placeholder: "0.00",
      hint: "How much to send?",
      type: "number",
      value: amount,
      setValue: setAmount,
    },
    {
      name: "title",
      label: "Transfer Title",
      placeholder: "e.g. Rent payment",
      hint: "Add a description",
      value: title,
      setValue: setTitle,
    },
  ];

  const currentField = fields[currentFieldIndex];
  const isComplete = accountNumber && recipientName && amount && title;

  // Get icon for each step
  const getStepIcon = (stepIndex: number) => {
    switch (stepIndex) {
      case 0: // Account Number
        return CreditCard;
      case 1: // Recipient Name
        return User;
      case 2: // Amount
        return DollarSign;
      case 3: // Transfer Title
        return FileText;
      default:
        return CreditCard;
    }
  };

  const StepIcon = getStepIcon(currentFieldIndex);

  useEffect(() => {
    if (supportLevel === "full") {
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [supportLevel]);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [currentFieldIndex]);

  // Auto-fill recipient name in partial support when suggestion is available
  useEffect(() => {
    if (supportLevel === "partial" && suggestedReceiverName && !recipientName) {
      setRecipientName(suggestedReceiverName);
    }
  }, [suggestedReceiverName, supportLevel]);

  const validateBankNumber = async (
    bankNumber: string,
  ): Promise<{
    valid: boolean;
    suggestion?: string;
    receiver_name?: string;
  }> => {
    try {
      // Remove spaces before validation
      const cleanedBankNumber = bankNumber.replace(/\s/g, "");

      const response = await fetch(`${API_BASE_URL}/validate_bank_number`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          bank_number: cleanedBankNumber,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Bank number validation error:", error);
      return { valid: true }; // Allow to proceed on error
    }
  };

  const validateFullname = async (
    bankNumber: string,
    fullname: string,
  ): Promise<{ valid: boolean; suggestion?: string }> => {
    try {
      // Remove spaces before validation
      const cleanedBankNumber = bankNumber.replace(/\s/g, "");

      const response = await fetch(`${API_BASE_URL}/validate_fullname`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          bank_number: cleanedBankNumber,
          fullname,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Fullname validation error:", error);
      return { valid: true }; // Allow to proceed on error
    }
  };

  const validateAmount = async (
    amount: number,
  ): Promise<{ valid: boolean; suggestion?: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/validate_amount`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          amount: amount,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Amount validation error:", error);
      return { valid: true }; // Allow to proceed on error
    }
  };

  const handleNextField = async () => {
    if (!currentField.value) return;

    // If user has already seen the error, allow them to proceed
    if (hasSeenError && validationError) {
      setValidationError(null);
      setHasSeenError(false);
      if (currentFieldIndex < fields.length - 1) {
        // Auto-fill recipient name if continuing from account number with suggestion
        if (currentFieldIndex === 0 && suggestedReceiverName) {
          setRecipientName(suggestedReceiverName);
          setSuggestedReceiverName(""); // Clear after use
        }
        setCurrentFieldIndex(currentFieldIndex + 1);
      }
      return;
    }

    setIsValidating(true);
    setValidationError(null);

    try {
      let validationResult: {
        valid: boolean;
        suggestion?: string;
        receiver_name?: string;
        error_position?: number;
      } = { valid: true, suggestion: undefined };

      // Validate based on current field
      if (currentFieldIndex === 0) {
        // Validate account number
        validationResult = (await validateBankNumber(accountNumber)) as any;
        if (!validationResult.valid) {
          const receiverName = (validationResult as any).receiver_name;
          let errorPos = (validationResult as any).error_position;

          // Fallback: calculate error position on frontend if backend doesn't provide it
          if (errorPos === undefined || errorPos === null) {
            const suggestion = validationResult.suggestion;
            if (suggestion && accountNumber) {
              for (
                let i = 0;
                i < Math.min(accountNumber.length, suggestion.length);
                i++
              ) {
                if (accountNumber[i] !== suggestion[i]) {
                  errorPos = i;
                  break;
                }
              }
            }
          }

          console.log("🔍 Validation Result:", validationResult);
          console.log("📍 Error Position:", errorPos);
          console.log("💡 Suggestion:", validationResult.suggestion);
          console.log("👤 Receiver Name:", receiverName);

          // Save receiver name for auto-fill on next step
          if (receiverName) {
            setSuggestedReceiverName(receiverName);
          }

          setValidationError({
            field: "accountNumber",
            message: receiverName
              ? `This account number looks similar to ${receiverName}'s account. Did you mean to send to them?`
              : validationResult.suggestion
                ? `This account number looks similar to: ${validationResult.suggestion}. Did you mean this one?`
                : "This account number appears to be invalid.",
            suggestion: validationResult.suggestion,
            receiverName: receiverName,
            userInput: accountNumber,
            errorPosition: errorPos,
          });
          setHasSeenError(true);
        }
      } else if (currentFieldIndex === 1) {
        // Validate recipient name
        validationResult = (await validateFullname(
          accountNumber,
          recipientName,
        )) as any;
        if (!validationResult.valid) {
          setValidationError({
            field: "name",
            message: validationResult.suggestion
              ? `The name doesn't match our records. Did you mean: ${validationResult.suggestion}?`
              : "The recipient name doesn't match previous transactions.",
            suggestion: validationResult.suggestion,
          });
          setHasSeenError(true);
        }
      } else if (currentFieldIndex === 2) {
        // Validate amount
        const amountValue = parseFloat(amount);
        validationResult = (await validateAmount(amountValue)) as any;
        if (!validationResult.valid) {
          setValidationError({
            field: "amount",
            message:
              "This amount is unusual compared to your typical transactions. Please verify.",
          });
          setHasSeenError(true);
        }
      }

      // If validation passed or user already saw error, proceed to next field
      if (validationResult.valid) {
        if (currentFieldIndex < fields.length - 1) {
          // Auto-fill recipient name if moving from account number to name field
          if (currentFieldIndex === 0 && suggestedReceiverName) {
            setRecipientName(suggestedReceiverName);
            setSuggestedReceiverName(""); // Clear after use
          }
          setCurrentFieldIndex(currentFieldIndex + 1);
        }
      }
    } catch (error) {
      console.error("Validation error:", error);
      // On error, allow user to proceed
      if (currentFieldIndex < fields.length - 1) {
        // Auto-fill recipient name if moving from account number to name field
        if (currentFieldIndex === 0 && suggestedReceiverName) {
          setRecipientName(suggestedReceiverName);
          setSuggestedReceiverName(""); // Clear after use
        }
        setCurrentFieldIndex(currentFieldIndex + 1);
      }
    } finally {
      setIsValidating(false);
    }
  };

  const handlePreviousField = () => {
    if (currentFieldIndex > 0) {
      setValidationError(null);
      setHasSeenError(false);

      // Clear suggested receiver name if going back from name field
      if (currentFieldIndex === 1) {
        setSuggestedReceiverName("");
      }

      setCurrentFieldIndex(currentFieldIndex - 1);
    }
  };

  const handleFieldChange = (value: string) => {
    // Format IBAN for account number field
    if (currentField.name === "accountNumber") {
      const formatted = formatIBAN(value);
      currentField.setValue(formatted);
    } else {
      currentField.setValue(value);
    }
    // Reset validation error when user changes the field
    if (validationError && validationError.field === currentField.name) {
      setValidationError(null);
      setHasSeenError(false);
    }
  };

  const applySuggestion = () => {
    if (validationError?.suggestion) {
      // Format IBAN suggestion for account number field
      const value =
        currentFieldIndex === 0
          ? formatIBAN(validationError.suggestion)
          : validationError.suggestion;
      currentField.setValue(value);

      // If applying bank number suggestion, save the receiver name for next step
      if (currentFieldIndex === 0 && validationError.receiverName) {
        setSuggestedReceiverName(validationError.receiverName);
      }

      setValidationError(null);
      setHasSeenError(false);
    }
  };

  const handleSend = () => {
    setShowConfirmation(true);
  };

  const handleConfirmTransaction = () => {
    // Reset form and go back to dashboard
    setAccountNumber("");
    setRecipientName("");
    setAmount("");
    setTitle("");
    setShowConfirmation(false);
    onBack();
  };

  const handleBackFromConfirmation = () => {
    setShowConfirmation(false);
  };

  if (showConfirmation) {
    return (
      <TransactionConfirmation
        onBack={handleBackFromConfirmation}
        onConfirm={handleConfirmTransaction}
        accountNumber={accountNumber}
        recipientName={recipientName}
        amount={amount}
        title={title}
        userId={userId}
      />
    );
  }

  const quickAmounts = [10, 50, 100, 500];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 relative">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-slate-200 px-4 py-4 z-20">
        <div className="flex items-center gap-3 max-w-2xl mx-auto">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-slate-900">Send Money</h1>
            {supportLevel !== "none" && (
              <p className="text-xs text-yellow-600 flex items-center gap-1">
                {supportLevel === "full" && (
                  <>
                    <Target className="w-3 h-3" />
                    Full Support Mode - Expert Guidance
                  </>
                )}
                {supportLevel === "partial" && (
                  <>
                    <Lightbulb className="w-3 h-3" />
                    Partial Support Mode
                  </>
                )}
              </p>
            )}
          </div>
        </div>
      </div>

      {supportLevel === "full" && (
        <div
          className="fixed inset-0 bg-black/20 z-10 pointer-events-none"
          style={{ top: "65px" }}
        />
      )}

      <div className="max-w-2xl mx-auto px-4 py-8 pb-12 relative z-11">
        {supportLevel === "full" && (
          <div className="mb-6 flex items-center gap-2 justify-center">
            {fields.map((_, index) => (
              <div key={index} className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentFieldIndex
                      ? "bg-yellow-400 w-3"
                      : index < currentFieldIndex
                        ? "bg-green-500"
                        : "bg-slate-300"
                  }`}
                />
                {index < fields.length - 1 && (
                  <div
                    className={`w-8 h-0.5 mx-1 transition-all ${
                      index < currentFieldIndex
                        ? "bg-green-500"
                        : "bg-slate-300"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {supportLevel === "full" ? (
          <div className="flex flex-col items-center justify-center min-h-96">
            <Card className="w-full max-w-md bg-white border-0 shadow-2xl relative z-20">
              <CardHeader className="pb-6 text-center">
                <div className="flex justify-center mb-3">
                  <div className="w-16 h-16 rounded-full bg-yellow-100 flex items-center justify-center">
                    <StepIcon className="w-8 h-8 text-yellow-600" />
                  </div>
                </div>
                <button
                  onClick={() => {
                    // Add delay before showing popup (500ms)
                    setTimeout(() => {
                      setShowFullSupportPopup(true);
                    }, 500);
                  }}
                  className="text-center w-full hover:opacity-80 transition-opacity cursor-pointer bg-transparent border-none p-0"
                >
                  <CardTitle className="text-2xl">
                    {currentField.label}
                  </CardTitle>
                </button>
                <p className="text-sm text-slate-500 mt-3">
                  {currentField.hint}
                </p>
                <p className="text-xs text-slate-400 mt-2 flex items-center justify-center gap-1">
                  <Lightbulb className="w-3 h-3" />
                  Click title above to simulate connection loss
                </p>
              </CardHeader>

              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-3">
                    Step {currentFieldIndex + 1} of {fields.length}
                  </label>

                  {currentField.name === "accountNumber" &&
                    recipients.length > 0 && (
                      <div className="mb-4">
                        <select
                          value=""
                          onChange={(e) => {
                            const r = recipients.find(
                              (x) => String(x.user_id) === e.target.value,
                            );
                            if (!r) return;
                            setAccountNumber(formatIBAN(r.bank_number));
                            setRecipientName(`${r.name} ${r.surname}`);
                            setCurrentFieldIndex(2);
                          }}
                          className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg text-base font-medium bg-white focus:outline-none focus:ring-4 focus:ring-blue-100"
                        >
                          <option value="">Choose a saved recipient…</option>
                          {recipients
                            .filter((r) => r.user_id !== userData?.user_id)
                            .map((r) => (
                              <option key={r.user_id} value={r.user_id}>
                                {r.name} {r.surname} · {r.bank_number}
                              </option>
                            ))}
                        </select>
                        <p className="text-xs text-slate-400 mt-2 text-center">
                          or enter details manually below
                        </p>
                      </div>
                    )}

                  <div className="relative">
                    <input
                      ref={inputRef}
                      type={currentField.type || "text"}
                      value={currentField.value}
                      onChange={(e) => handleFieldChange(e.target.value)}
                      placeholder={currentField.placeholder}
                      className={`w-full px-4 py-3 border-2 rounded-lg text-base font-medium transition-all focus:outline-none focus:ring-4 bg-white ${
                        currentField.name === "accountNumber"
                          ? "font-mono tracking-wider"
                          : ""
                      } ${
                        validationError &&
                        validationError.field === currentField.name
                          ? "border-yellow-500 focus:ring-yellow-200"
                          : "border-yellow-400 focus:ring-yellow-200"
                      }`}
                      disabled={isValidating}
                    />
                  </div>

                  {validationError &&
                    validationError.field === currentField.name && (
                      <div className="mt-3 p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                        <div className="flex gap-3">
                          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-yellow-900 mb-2">
                              Please Review
                            </p>
                            {validationError.receiverName ? (
                              <div className="space-y-2">
                                <p className="text-xs text-yellow-800">
                                  Similar to{" "}
                                  <span className="font-bold">
                                    {validationError.receiverName}
                                  </span>
                                  . Did you mean them?
                                </p>
                                {validationError.userInput &&
                                  validationError.suggestion && (
                                    <div className="bg-white rounded-md p-2 border border-yellow-200 space-y-1">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-yellow-700 font-medium w-12 shrink-0">
                                          You:
                                        </span>
                                        <div className="font-mono text-xs leading-relaxed">
                                          {validationError.userInput
                                            .split("")
                                            .map((char, idx) => (
                                              <span
                                                key={idx}
                                                className={
                                                  validationError.errorPosition !==
                                                    undefined &&
                                                  idx >=
                                                    validationError.errorPosition
                                                    ? "text-red-700 font-extrabold bg-red-100 border-b-[3px] border-red-600 px-px rounded-sm"
                                                    : "text-slate-700"
                                                }
                                              >
                                                {char}
                                              </span>
                                            ))}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-green-700 font-medium w-12 shrink-0">
                                          Them:
                                        </span>
                                        <div className="font-mono text-xs leading-relaxed">
                                          {validationError.suggestion
                                            .split("")
                                            .map((char, idx) => (
                                              <span
                                                key={idx}
                                                className={
                                                  validationError.errorPosition !==
                                                    undefined &&
                                                  idx >=
                                                    validationError.errorPosition
                                                    ? "text-green-700 font-extrabold bg-green-100 border-b-[3px] border-green-600 px-px rounded-sm"
                                                    : "text-slate-700"
                                                }
                                              >
                                                {char}
                                              </span>
                                            ))}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                              </div>
                            ) : (
                              <p className="text-sm text-yellow-800">
                                {validationError.message}
                              </p>
                            )}
                            {validationError.suggestion && (
                              <button
                                onClick={applySuggestion}
                                className="mt-2 px-2.5 py-1.5 text-xs font-semibold text-yellow-900 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors"
                              >
                                Use{" "}
                                {validationError.receiverName
                                  ? "their"
                                  : "correct"}{" "}
                                account
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                </div>

                {currentFieldIndex === 2 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-500 mb-3 uppercase">
                      Quick Select
                    </p>
                    <div className="grid grid-cols-4 gap-2">
                      {quickAmounts.map((q) => (
                        <button
                          key={q}
                          onClick={() => handleFieldChange(q.toString())}
                          disabled={isValidating}
                          className={`p-3 rounded-lg font-semibold transition-all text-sm ${
                            amount === q.toString()
                              ? "bg-yellow-400 text-slate-900 ring-2 ring-yellow-600"
                              : "bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50"
                          }`}
                        >
                          {q} zł
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {isComplete && (
                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200">
                    <p className="text-xs font-bold text-green-700 mb-2">
                      READY TO SEND
                    </p>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Amount:</span>
                        <span className="font-bold text-slate-900">
                          {amount} zł
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">To:</span>
                        <span className="font-bold text-slate-900">
                          {recipientName}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Account:</span>
                        <span className="font-mono text-xs text-slate-900 tracking-wider">
                          {accountNumber}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  {currentFieldIndex > 0 && (
                    <Button
                      onClick={handlePreviousField}
                      variant="outline"
                      className="flex-1 border-slate-300 py-3"
                      disabled={isValidating}
                    >
                      Back
                    </Button>
                  )}
                  {currentFieldIndex === fields.length - 1 ? (
                    <Button
                      onClick={handleSend}
                      disabled={!isComplete || isValidating}
                      className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isValidating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                          Validating...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Send
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      onClick={handleNextField}
                      disabled={!currentField.value || isValidating}
                      className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isValidating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                          Validating...
                        </>
                      ) : hasSeenError && validationError ? (
                        <>
                          Continue Anyway
                          <ArrowRight className="w-4 h-4" />
                        </>
                      ) : (
                        <>
                          Next
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card className="bg-white border-0 shadow-lg">
            <CardHeader className="pb-6">
              <button
                onClick={() => {
                  // Add delay before showing popup (500ms)
                  setTimeout(() => {
                    setShowSimplePopup(true);
                  }, 500);
                }}
                className="text-left w-full hover:opacity-80 transition-opacity cursor-pointer bg-transparent border-none p-0"
              >
                <CardTitle className="text-2xl">Transfer Details</CardTitle>
              </button>
              <p className="text-sm text-slate-500 mt-2">
                Fill in the information below to send money
              </p>
            </CardHeader>

            <CardContent className="space-y-6">
              {recipients.length > 0 && (
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-3">
                    Quick select recipient
                  </label>
                  <select
                    value=""
                    onChange={(e) => {
                      const r = recipients.find(
                        (x) => String(x.user_id) === e.target.value,
                      );
                      if (!r) return;
                      setAccountNumber(formatIBAN(r.bank_number));
                      setRecipientName(`${r.name} ${r.surname}`);
                    }}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg text-base font-medium bg-white focus:outline-none focus:ring-4 focus:ring-blue-100"
                  >
                    <option value="">Choose a saved recipient…</option>
                    {recipients
                      .filter((r) => r.user_id !== userData?.user_id)
                      .map((r) => (
                        <option key={r.user_id} value={r.user_id}>
                          {r.name} {r.surname} · {r.bank_number}
                        </option>
                      ))}
                  </select>
                  <p className="text-xs text-slate-400 mt-2">
                    or fill the fields manually below
                  </p>
                </div>
              )}
              {fields.map((field) => {
                const fieldError =
                  field.name === "accountNumber"
                    ? accountNumberError
                    : field.name === "name"
                      ? recipientNameError
                      : field.name === "amount"
                        ? amountError
                        : null;
                const isValidatingField =
                  field.name === "accountNumber"
                    ? isValidatingPartial.accountNumber
                    : field.name === "name"
                      ? isValidatingPartial.recipientName
                      : field.name === "amount"
                        ? isValidatingPartial.amount
                        : false;

                return (
                  <div key={field.name}>
                    <label className="block text-sm font-semibold text-slate-700 mb-3">
                      {field.label}
                    </label>

                    <div className="relative flex items-center">
                      <input
                        type={field.type || "text"}
                        value={field.value}
                        onChange={(e) => {
                          // Apply IBAN formatting for account number field
                          if (field.name === "accountNumber") {
                            const formatted = formatIBAN(e.target.value);
                            field.setValue(formatted);
                            setAccountNumberError(null);
                          } else {
                            field.setValue(e.target.value);
                            if (field.name === "name") {
                              setRecipientNameError(null);
                            } else if (field.name === "amount") {
                              setAmountError(null);
                            }
                          }
                        }}
                        onBlur={async () => {
                          // Validate on blur for partial support mode
                          if (supportLevel === "partial" && field.value) {
                            if (field.name === "accountNumber") {
                              setIsValidatingPartial((prev) => ({
                                ...prev,
                                accountNumber: true,
                              }));
                              const result = await validateBankNumber(
                                field.value,
                              );
                              setIsValidatingPartial((prev) => ({
                                ...prev,
                                accountNumber: false,
                              }));

                              if (!result.valid) {
                                const receiverName = (result as any)
                                  .receiver_name;
                                let errorPos = (result as any).error_position;

                                if (
                                  errorPos === undefined ||
                                  errorPos === null
                                ) {
                                  const suggestion = result.suggestion;
                                  if (suggestion && field.value) {
                                    for (
                                      let i = 0;
                                      i <
                                      Math.min(
                                        field.value.length,
                                        suggestion.length,
                                      );
                                      i++
                                    ) {
                                      if (field.value[i] !== suggestion[i]) {
                                        errorPos = i;
                                        break;
                                      }
                                    }
                                  }
                                }

                                setAccountNumberError({
                                  field: "accountNumber",
                                  message: receiverName
                                    ? `This account number looks similar to ${receiverName}'s account. Did you mean to send to them?`
                                    : result.suggestion
                                      ? `This account number looks similar to: ${result.suggestion}. Did you mean this one?`
                                      : "This account number appears to be invalid.",
                                  suggestion: result.suggestion,
                                  receiverName: receiverName,
                                  userInput: field.value,
                                  errorPosition: errorPos,
                                });

                                if (receiverName) {
                                  setSuggestedReceiverName(receiverName);
                                }
                              }
                            } else if (field.name === "name") {
                              if (accountNumber) {
                                setIsValidatingPartial((prev) => ({
                                  ...prev,
                                  recipientName: true,
                                }));
                                const result = await validateFullname(
                                  accountNumber,
                                  field.value,
                                );
                                setIsValidatingPartial((prev) => ({
                                  ...prev,
                                  recipientName: false,
                                }));

                                if (!result.valid) {
                                  setRecipientNameError({
                                    field: "recipientName",
                                    message: result.suggestion
                                      ? `The name doesn't match our records. Did you mean: ${result.suggestion}?`
                                      : "The recipient name doesn't match previous transactions.",
                                    suggestion: result.suggestion,
                                  });
                                }
                              }
                            } else if (field.name === "amount") {
                              const amountValue = parseFloat(field.value);
                              if (!isNaN(amountValue)) {
                                setIsValidatingPartial((prev) => ({
                                  ...prev,
                                  amount: true,
                                }));
                                const result =
                                  await validateAmount(amountValue);
                                setIsValidatingPartial((prev) => ({
                                  ...prev,
                                  amount: false,
                                }));

                                if (!result.valid) {
                                  setAmountError({
                                    field: "amount",
                                    message:
                                      "This amount is unusual compared to your typical transactions. Please verify.",
                                  });
                                }
                              }
                            }
                          }
                        }}
                        placeholder={field.placeholder}
                        disabled={isValidatingField}
                        className={`w-full px-4 py-3 border-2 rounded-lg text-base transition-all focus:outline-none bg-white ${
                          field.name === "accountNumber"
                            ? "font-mono tracking-wider"
                            : ""
                        } ${
                          fieldError
                            ? "border-yellow-500 focus:border-yellow-600"
                            : showDraftRestored && field.value
                              ? "border-green-500 focus:border-green-600 animate-pulse"
                              : "border-slate-200 focus:border-yellow-400 hover:border-slate-300"
                        }`}
                      />
                      {isValidatingField && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          <div className="w-5 h-5 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                      )}
                      {showDraftRestored &&
                        field.value &&
                        !isValidatingField && (
                          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                            <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                              <svg
                                className="w-4 h-4 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            </div>
                          </div>
                        )}
                    </div>

                    {fieldError && (
                      <div className="mt-3 p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                        <div className="flex gap-3">
                          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-yellow-900 mb-2">
                              Please Review
                            </p>
                            {fieldError.receiverName ? (
                              <div className="space-y-2">
                                <p className="text-xs text-yellow-800">
                                  Similar to{" "}
                                  <span className="font-bold">
                                    {fieldError.receiverName}
                                  </span>
                                  . Did you mean them?
                                </p>
                                {fieldError.userInput &&
                                  fieldError.suggestion && (
                                    <div className="bg-white rounded-md p-2 border border-yellow-200 space-y-1">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-yellow-700 font-medium w-12 shrink-0">
                                          You:
                                        </span>
                                        <div className="font-mono text-xs leading-relaxed">
                                          {fieldError.userInput
                                            .split("")
                                            .map((char, idx) => (
                                              <span
                                                key={idx}
                                                className={
                                                  fieldError.errorPosition !==
                                                    undefined &&
                                                  idx >=
                                                    fieldError.errorPosition
                                                    ? "text-red-700 font-extrabold bg-red-100 border-b-[3px] border-red-600 px-px rounded-sm"
                                                    : "text-slate-700"
                                                }
                                              >
                                                {char}
                                              </span>
                                            ))}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-green-700 font-medium w-12 shrink-0">
                                          Them:
                                        </span>
                                        <div className="font-mono text-xs leading-relaxed">
                                          {fieldError.suggestion
                                            .split("")
                                            .map((char, idx) => (
                                              <span
                                                key={idx}
                                                className={
                                                  fieldError.errorPosition !==
                                                    undefined &&
                                                  idx >=
                                                    fieldError.errorPosition
                                                    ? "text-green-700 font-extrabold bg-green-100 border-b-[3px] border-green-600 px-px rounded-sm"
                                                    : "text-slate-700"
                                                }
                                              >
                                                {char}
                                              </span>
                                            ))}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                              </div>
                            ) : (
                              <p className="text-sm text-yellow-800">
                                {fieldError.message}
                              </p>
                            )}
                            {fieldError.suggestion && (
                              <button
                                onClick={() => {
                                  if (field.name === "accountNumber") {
                                    const formatted = formatIBAN(
                                      fieldError.suggestion!,
                                    );
                                    setAccountNumber(formatted);
                                    if (fieldError.receiverName) {
                                      setSuggestedReceiverName(
                                        fieldError.receiverName,
                                      );
                                    }
                                    setAccountNumberError(null);
                                  } else if (field.name === "name") {
                                    setRecipientName(fieldError.suggestion!);
                                    setRecipientNameError(null);
                                  }
                                }}
                                className="mt-2 px-2.5 py-1.5 text-xs font-semibold text-yellow-900 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors"
                              >
                                Use{" "}
                                {fieldError.receiverName
                                  ? "their"
                                  : "suggested"}{" "}
                                {field.name === "accountNumber"
                                  ? "account"
                                  : "name"}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {isComplete && (
                <div className="p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                  <p className="text-xs text-slate-500 font-semibold mb-3">
                    TRANSFER SUMMARY
                  </p>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600">Amount:</span>
                      <span className="font-bold text-slate-900">
                        {amount} zł
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600">To:</span>
                      <span className="font-bold text-slate-900">
                        {recipientName}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600">Account:</span>
                      <span className="font-mono text-xs text-slate-600 tracking-wider">
                        {accountNumber}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600">Title:</span>
                      <span className="text-sm text-slate-900">{title}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-6">
                <Button
                  onClick={onBack}
                  variant="outline"
                  className="flex-1 border-slate-300 py-3"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSend}
                  disabled={
                    !isComplete ||
                    isValidatingPartial.accountNumber ||
                    isValidatingPartial.recipientName ||
                    isValidatingPartial.amount
                  }
                  className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isValidatingPartial.accountNumber ||
                  isValidatingPartial.recipientName ||
                  isValidatingPartial.amount ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send Transfer
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Draft Restored Notification - Bottom Right */}
      {showDraftRestored && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-2">
          <div className="bg-green-500 text-white px-4 py-3 rounded-lg shadow-2xl flex items-center gap-3 max-w-sm">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-sm">Draft Restored!</p>
              <p className="text-xs text-white/90">
                Data recovered successfully
              </p>
            </div>
            <button
              onClick={() => setShowDraftRestored(false)}
              className="hover:bg-white/20 rounded p-1 transition-colors"
            >
              <svg
                className="w-4 h-4 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Connection Lost Popup */}
      {showSimplePopup && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 z-40"
            onClick={() => setShowSimplePopup(false)}
          />

          {/* Popup Container */}
          <div className="fixed inset-x-0 top-20 max-w-md mx-auto z-50">
            <div className="mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h3 className="font-semibold text-slate-900 text-xl mb-2">
                  Connection Lost
                </h3>
                <p className="text-sm text-slate-500">No internet connection</p>
              </div>
              <p className="text-sm text-slate-600 mb-6 text-center">
                Your internet connection was interrupted. Would you like to save
                your progress as a draft and continue when connection is
                restored?
              </p>
              <div className="bg-slate-50 rounded-lg p-4 mb-6 space-y-2">
                <p className="text-xs font-semibold text-slate-700">
                  Draft will include:
                </p>
                {accountNumber && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    Account: {accountNumber}
                  </div>
                )}
                {recipientName && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    Recipient: {recipientName}
                  </div>
                )}
                {amount && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    Amount: {amount} zł
                  </div>
                )}
                {title && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    Title: {title}
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-3">
                <Button
                  onClick={() => {
                    setIsSavingDraft(true);

                    // Add 1 second delay before saving
                    setTimeout(() => {
                      // Save draft to localStorage
                      const draft = {
                        accountNumber,
                        recipientName,
                        amount,
                        title,
                        supportLevel: "none",
                        timestamp: Date.now(),
                      };
                      localStorage.setItem(
                        "transferDraft",
                        JSON.stringify(draft),
                      );
                      // Set offline flag
                      localStorage.setItem("offlineMode", "true");
                      // Close popup and redirect
                      setShowSimplePopup(false);
                      setIsSavingDraft(false);
                      onBack();
                    }, 1000);
                  }}
                  disabled={isSavingDraft}
                  className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSavingDraft ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                      Saving Draft...
                    </>
                  ) : (
                    "Save Draft & Continue"
                  )}
                </Button>
                <Button
                  onClick={() => setShowSimplePopup(false)}
                  variant="outline"
                  className="w-full border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Full Support Offline Popup */}
      {showFullSupportPopup && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 z-50"
            onClick={() => setShowFullSupportPopup(false)}
          />

          {/* Popup Container */}
          <div className="fixed inset-x-0 top-20 max-w-md mx-auto z-50 px-4">
            <div className="bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                  <svg
                    className="w-8 h-8 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-slate-900 text-xl mb-2">
                  Connection Lost
                </h3>
                <p className="text-sm text-slate-500">
                  Your internet connection was interrupted
                </p>
              </div>
              <p className="text-sm text-slate-600 mb-6 text-center">
                Don't worry! We've saved your progress. You can continue where
                you left off when the connection is restored.
              </p>
              <div className="bg-yellow-50 rounded-lg p-4 mb-6 border-2 border-yellow-200">
                <p className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                  <Save className="w-3 h-3" />
                  Progress Saved
                </p>
                <div className="space-y-1 text-xs text-slate-600">
                  {accountNumber && (
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      Account: {accountNumber}
                    </div>
                  )}
                  {recipientName && (
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      Name: {recipientName}
                    </div>
                  )}
                  {amount && (
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      Amount: {amount} zł
                    </div>
                  )}
                  {title && (
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      Title: {title}
                    </div>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                    Current step: {currentFieldIndex + 1} of {fields.length}
                  </div>
                </div>
              </div>
              <div className="flex flex-col gap-3">
                <Button
                  onClick={() => {
                    setIsSavingDraft(true);

                    // Add 1 second delay before saving
                    setTimeout(() => {
                      // Save draft to localStorage with current step and support level
                      const draft = {
                        accountNumber: accountNumber.replace(/\s/g, ""),
                        recipientName,
                        amount,
                        title,
                        currentStep: currentFieldIndex,
                        supportLevel: "full",
                        timestamp: Date.now(),
                      };
                      localStorage.setItem(
                        "transferDraft",
                        JSON.stringify(draft),
                      );
                      // Set offline flag
                      localStorage.setItem("offlineMode", "true");
                      // Close popup and redirect
                      setShowFullSupportPopup(false);
                      setIsSavingDraft(false);
                      onBack();
                    }, 1000);
                  }}
                  disabled={isSavingDraft}
                  className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSavingDraft ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                      Saving Draft...
                    </>
                  ) : (
                    "Save Draft & Continue"
                  )}
                </Button>
                <Button
                  onClick={() => setShowFullSupportPopup(false)}
                  variant="outline"
                  className="w-full border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
