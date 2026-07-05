import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes } from 'react'

type GoogleLoginButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  isLoading?: boolean
}

export function GoogleLoginButton({
  isLoading = false,
  disabled,
  ...props
}: GoogleLoginButtonProps) {
  return (
    <button
      className="google-login-button"
      disabled={disabled || isLoading}
      type="button"
      {...props}
    >
      {isLoading ? (
        <Loader2 aria-hidden="true" className="button-spinner" size={20} />
      ) : (
        <img aria-hidden="true" className="google-mark" src="/google.svg" alt="" />
      )}
      <span>{isLoading ? 'Opening Google' : 'Continue with Google'}</span>
    </button>
  )
}
