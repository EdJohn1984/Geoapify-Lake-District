"use client"

import { useWizard } from "./wizard-context"
import { cn } from "@/lib/utils"

export function StepIndicator() {
  const { currentStep, totalSteps, goToStep } = useWizard()

  return (
    <div className="flex items-center justify-center mb-8">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div key={index} className="flex items-center">
          <div
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
              currentStep === index
                ? "bg-primary text-primary-foreground"
                : currentStep > index
                  ? "bg-primary/80 text-primary-foreground cursor-pointer"
                  : "bg-muted text-muted-foreground",
            )}
            onClick={() => currentStep > index && goToStep(index)}
            role={currentStep > index ? "button" : undefined}
            tabIndex={currentStep > index ? 0 : undefined}
            aria-label={currentStep > index ? `Go to step ${index + 1}` : undefined}
          >
            {index + 1}
          </div>
          {index < totalSteps - 1 && (
            <div className={cn("h-1 w-10", currentStep > index ? "bg-primary/80" : "bg-muted")} />
          )}
        </div>
      ))}
    </div>
  )
}
