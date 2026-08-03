import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { LoginForm, type LoginFormValues } from "@/features/auth";
import { ApiError } from "@/shared/lib/api-error";
import { fetchHostContext, type HostContext } from "@/shared/lib/auth";

import { useAuth } from "../providers/AuthProvider";

export function LoginPage() {
  const { status, login, platformLogin } = useAuth();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hostType, setHostType] = useState<HostContext["host_type"] | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const context = await fetchHostContext();
        if (!cancelled) setHostType(context.host_type);
      } catch {
        // Falls back to the institution flow — the far more common case,
        // and every other error path on this page already surfaces
        // failures through the form itself, not a page-level crash.
        if (!cancelled) setHostType("institution");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "authenticated") return <Navigate to="/" replace />;

  const isPlatformHost = hostType === "platform";

  const handleSubmit = async (values: LoginFormValues) => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      if (isPlatformHost) {
        await platformLogin(values.emailOrPhone, values.password);
      } else {
        await login(values.emailOrPhone, values.password);
      }
      navigate("/", { replace: true });
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-md">
        <h1 className="mb-6 text-2xl font-semibold text-text">
          {isPlatformHost ? "Platform Administrator Sign In" : "Sign in to EduCore"}
        </h1>
        <LoginForm
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          errorMessage={errorMessage}
        />
        {!isPlatformHost && (
          <p className="mt-4 text-center text-sm text-text">
            <Link to="/forgot-password" className="text-primary hover:underline">
              Forgot your password?
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
