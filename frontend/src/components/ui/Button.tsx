import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-300',
          'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2',
          'disabled:opacity-50 disabled:pointer-events-none',
          'active:scale-95',
          {
            'gradient-primary text-white hover:shadow-glow border-0': variant === 'primary',
            'bg-transparent border-2 border-primary/30 text-primary hover:bg-primary/10 hover:border-primary/50':
              variant === 'outline',
            'bg-muted text-foreground hover:bg-muted/80':
              variant === 'secondary',
            'bg-transparent text-foreground hover:bg-muted/50':
              variant === 'ghost',
          },
          {
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-5 py-2.5 text-base': size === 'md',
            'px-7 py-3.5 text-lg font-semibold': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }
