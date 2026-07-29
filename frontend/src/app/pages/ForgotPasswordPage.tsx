import { useState } from "react";
import { Link } from "react-router-dom";

import {
  ForgotPasswordForm,
  useRequestPasswordReset,
  type ForgotPasswordFormValues,
} from "@/features/auth";

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const { mutateAsync, isPending } = useRequestPasswordReset();

  const handleSubmit = async (values: ForgotPasswordFormValues) => {
    // Always a generic ack regardless of whether the identifier matched a
    // user (docs/authentication.md §6 — the backend's own response is
    // already this generic; the frontend just relays it as-is rather than
    // branching on a success/failure it never gets to see).
    await mutateAsync({ emailOrPhone: values.emailOrPhone });
    setSubmitted(true);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-md">
        <h1 className="mb-6 text-2xl font-semibold text-text">Reset your password</h1>
        {submitted ? (
          <p className="text-text">If an account exists, a reset link has been sent.</p>
        ) : (
          <ForgotPasswordForm onSubmit={handleSubmit} isSubmitting={isPending} />
        )}
        <p className="mt-4 text-center text-sm text-text">
          <Link to="/login" className="text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
