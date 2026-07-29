import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import {
  ResetPasswordForm,
  useConfirmPasswordReset,
  type ResetPasswordFormValues,
} from "@/features/auth";
import { ApiError } from "@/shared/lib/api-error";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const { mutateAsync, isPending } = useConfirmPasswordReset();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 text-center shadow-md">
          <p className="text-text">This reset link is missing its token.</p>
          <Link to="/forgot-password" className="mt-4 inline-block text-primary hover:underline">
            Request a new one
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (values: ResetPasswordFormValues) => {
    setErrorMessage(null);
    try {
      await mutateAsync({ token, newPassword: values.newPassword });
      navigate("/login", { replace: true });
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-md">
        <h1 className="mb-6 text-2xl font-semibold text-text">Set a new password</h1>
        <ResetPasswordForm
          onSubmit={handleSubmit}
          isSubmitting={isPending}
          errorMessage={errorMessage}
        />
      </div>
    </div>
  );
}
