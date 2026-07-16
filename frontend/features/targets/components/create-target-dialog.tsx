"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTarget } from "@/features/targets/hooks/use-targets";
import {
  createTargetSchema,
  type CreateTargetFormValues,
} from "@/features/targets/schemas/target-schema";

/** Field-level backend failures a user can act on by editing the value. */
function isFieldLevelError(code: string): boolean {
  return code === "VALIDATION_ERROR" || code === "CONFLICT";
}

export function CreateTargetDialog({
  trigger,
}: {
  /** Custom trigger element (e.g. an EmptyState CTA). Defaults to a "New Target" button. */
  trigger?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const { mutate, isPending } = useCreateTarget();
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<CreateTargetFormValues>({
    resolver: zodResolver(createTargetSchema),
    defaultValues: { target: "" },
  });

  function handleOpenChange(next: boolean) {
    if (isPending) return; // prevent closing mid-submit
    setOpen(next);
    if (!next) reset();
  }

  function onSubmit(values: CreateTargetFormValues) {
    mutate(values, {
      onSuccess: () => {
        toast.success("Target created");
        reset();
        setOpen(false);
      },
      onError: (error) => {
        if (isFieldLevelError(error.code)) {
          setError("target", { type: "server", message: error.message });
          return;
        }
        toast.error(error.message);
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <Plus className="size-4" aria-hidden="true" />
            New Target
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add a target</DialogTitle>
          <DialogDescription>
            Register an IPv4 address, IPv4 CIDR range, or hostname for
            assessment. The platform validates and classifies the value
            before it is added to inventory.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
          noValidate
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="target">Target</Label>
            <Input
              id="target"
              placeholder="192.168.1.10, 10.0.0.0/24, or example.com"
              autoComplete="off"
              autoFocus
              disabled={isPending}
              aria-invalid={Boolean(errors.target)}
              aria-describedby={errors.target ? "target-error" : undefined}
              {...register("target")}
            />
            {errors.target && (
              <p id="target-error" role="alert" className="text-sm text-destructive">
                {errors.target.message}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Adding…" : "Add Target"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
