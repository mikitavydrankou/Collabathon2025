"use client";

import { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  Send,
  ChevronRight,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SendMoneyPageProps {
  onBack: () => void;
  supportLevel?: "full" | "partial" | "none";
}

interface ValidationError {
  field: string;
  message: string;
  suggestion?: string;
  receiverName?: string;
}

export default function SendMoneyPage({
  onBack,
  supportLevel = "none",
}: SendMoneyPageProps) {
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0);

  const [accountNumber, setAccountNumber] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [amount, setAmount] = useState("");
  const [title, setTitle] = useState("");

  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] =
    useState<ValidationError | null>(null);
  const [hasSeenError, setHasSeenError] = useState(false);
  const [suggestedReceiverName, setSuggestedReceiverName] =
    useState<string>("");

  const inputRef = useRef<HTMLInputElement | null>(null);

  // TODO: Replace with actual user ID from authentication
  const userId = 1;

  const fields = [
    {
      name: "accountNumber",
      label: "Account Number (IBAN)",
      placeholder: "DE89 3704 0044 0532...",
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

  useEffect(() => {
    if (supportLevel === "full") {
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [supportLevel]);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [currentFieldIndex]);

  const validateBankNumber = async (
    bankNumber: string,
  ): Promise<{
    valid: boolean;
    suggestion?: string;
    receiver_name?: string;
  }> => {
    try {
      const response = await fetch(
        "http://localhost:8000/validate_bank_number",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: userId,
            bank_number: bankNumber,
          }),
        },
      );

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
    fullname: string,
    bankNumber: string,
  ): Promise<{ valid: boolean; suggestion?: string }> => {
    try {
      const response = await fetch("http://localhost:8000/validate_fullname", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          bank_number: bankNumber,
          fullname: fullname,
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
      const response = await fetch("http://localhost:8000/validate_amount", {
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
      let validationResult = { valid: true, suggestion: undefined };

      // Validate based on current field
      if (currentFieldIndex === 0) {
        // Validate account number
        validationResult = await validateBankNumber(accountNumber);
        if (!validationResult.valid) {
          const receiverName = (validationResult as any).receiver_name;

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
          });
          setHasSeenError(true);
        }
      } else if (currentFieldIndex === 1) {
        // Validate recipient name
        validationResult = await validateFullname(recipientName, accountNumber);
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
        validationResult = await validateAmount(amountValue);
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
    currentField.setValue(value);
    // Reset validation error when user changes the field
    if (validationError && validationError.field === currentField.name) {
      setValidationError(null);
      setHasSeenError(false);
    }
  };

  const applySuggestion = () => {
    if (validationError?.suggestion) {
      currentField.setValue(validationError.suggestion);

      // If applying bank number suggestion, save the receiver name for next step
      if (currentFieldIndex === 0 && validationError.receiverName) {
        setSuggestedReceiverName(validationError.receiverName);
      }

      setValidationError(null);
      setHasSeenError(false);
    }
  };

  const handleSend = () => {
    alert(
      `Transfer of €${amount} to ${recipientName} completed!\nAccount: ${accountNumber}\nDescription: ${title}`,
    );
    onBack();
  };

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
              <p className="text-xs text-yellow-600">
                {supportLevel === "full" &&
                  "🎯 Full Support Mode - Expert Guidance"}
                {supportLevel === "partial" && "💡 Partial Support Mode"}
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
                <div className="text-4xl mb-3">📍</div>
                <CardTitle className="text-2xl">{currentField.label}</CardTitle>
                <p className="text-sm text-slate-500 mt-3">
                  {currentField.hint}
                </p>
              </CardHeader>

              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-3">
                    Step {currentFieldIndex + 1} of {fields.length}
                  </label>

                  <div className="relative">
                    <input
                      ref={inputRef}
                      type={currentField.type || "text"}
                      value={currentField.value}
                      onChange={(e) => handleFieldChange(e.target.value)}
                      placeholder={currentField.placeholder}
                      className={`w-full px-4 py-3 border-2 rounded-lg text-base font-medium transition-all focus:outline-none focus:ring-4 bg-white ${
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
                                <p className="text-sm text-yellow-800">
                                  This account number looks similar to{" "}
                                  <span className="font-bold text-yellow-900">
                                    {validationError.receiverName}'s
                                  </span>{" "}
                                  account.
                                </p>
                                <p className="text-sm text-yellow-800">
                                  Did you mean to send to them?
                                </p>
                              </div>
                            ) : (
                              <p className="text-sm text-yellow-800">
                                {validationError.message}
                              </p>
                            )}
                            {validationError.suggestion && (
                              <button
                                onClick={applySuggestion}
                                className="mt-3 px-3 py-1.5 text-sm font-semibold text-yellow-900 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors"
                              >
                                Use{" "}
                                {validationError.receiverName
                                  ? "their"
                                  : "suggested"}{" "}
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
                          €{q}
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
                          €{amount}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">To:</span>
                        <span className="font-bold text-slate-900">
                          {recipientName}
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
              <CardTitle className="text-2xl">Transfer Details</CardTitle>
              <p className="text-sm text-slate-500 mt-2">
                Fill in the information below to send money
              </p>
            </CardHeader>

            <CardContent className="space-y-6">
              {fields.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-semibold text-slate-700 mb-3">
                    {field.label}
                  </label>

                  <div className="relative flex items-center">
                    <input
                      type={field.type || "text"}
                      value={field.value}
                      onChange={(e) => field.setValue(e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg text-base transition-all focus:outline-none focus:border-yellow-400 bg-white hover:border-slate-300"
                    />
                  </div>
                </div>
              ))}

              {isComplete && (
                <div className="p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                  <p className="text-xs text-slate-500 font-semibold mb-3">
                    TRANSFER SUMMARY
                  </p>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600">Amount:</span>
                      <span className="font-bold text-slate-900">
                        €{amount}
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
                      <span className="text-mono text-xs text-slate-600">
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
                  disabled={!isComplete}
                  className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send Transfer
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
