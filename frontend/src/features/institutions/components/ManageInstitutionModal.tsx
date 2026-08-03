import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { Modal } from "@/shared/components/Modal";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";
import { ApiError } from "@/shared/lib/api";

import { useAddCustomDomain } from "../api/useAddCustomDomain";
import { useSetIsolationTier } from "../api/useSetIsolationTier";
import { useVerifyDomain } from "../api/useVerifyDomain";
import type { Domain, Institution, IsolationTier } from "../types";

interface ManageInstitutionModalProps {
  institution: Institution | null;
  onClose: () => void;
}

const TIER_OPTIONS = [
  { value: "shared_row", label: "Shared database, row isolation" },
  { value: "dedicated_db", label: "Dedicated database, shared infrastructure" },
  { value: "dedicated_infra", label: "Dedicated infrastructure" },
];

export function ManageInstitutionModal({ institution, onClose }: ManageInstitutionModalProps) {
  return (
    <Modal open={institution !== null} onClose={onClose} title="Manage institution">
      {/* Keyed on the institution so every field resets to fresh defaults
       * when a different row's "Manage" button is clicked, instead of
       * carrying over the previous institution's local form state. */}
      {institution && (
        <ManageInstitutionModalBody key={institution.id} institution={institution} />
      )}
    </Modal>
  );
}

function ManageInstitutionModalBody({ institution }: { institution: Institution }) {
  const [tier, setTier] = useState<IsolationTier>(institution.isolation_tier);
  const [dbAlias, setDbAlias] = useState(institution.db_alias);
  const [tierError, setTierError] = useState<string | null>(null);

  const [hostname, setHostname] = useState("");
  const [addedDomain, setAddedDomain] = useState<Domain | null>(null);
  const [domainError, setDomainError] = useState<string | null>(null);

  const [resolvedRecords, setResolvedRecords] = useState("");
  const [verifiedDomain, setVerifiedDomain] = useState<Domain | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const { mutateAsync: setIsolationTier, isPending: isSettingTier } = useSetIsolationTier();
  const { mutateAsync: addCustomDomain, isPending: isAddingDomain } = useAddCustomDomain();
  const { mutateAsync: verifyDomain, isPending: isVerifying } = useVerifyDomain();

  async function handleSetTier() {
    setTierError(null);
    try {
      await setIsolationTier({ institutionId: institution.id, input: { tier, db_alias: dbAlias } });
    } catch (error) {
      setTierError(error instanceof ApiError ? error.message : "Could not update the isolation tier.");
    }
  }

  async function handleAddDomain() {
    setDomainError(null);
    setAddedDomain(null);
    setVerifiedDomain(null);
    try {
      const domain = await addCustomDomain({ institutionId: institution.id, input: { hostname } });
      setAddedDomain(domain);
      setHostname("");
    } catch (error) {
      setDomainError(error instanceof ApiError ? error.message : "Could not add this domain.");
    }
  }

  async function handleVerifyDomain() {
    if (!addedDomain) return;
    setVerifyError(null);
    try {
      const records = resolvedRecords
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      const domain = await verifyDomain({
        domainId: addedDomain.id,
        input: { resolved_txt_records: records },
      });
      setVerifiedDomain(domain);
    } catch (error) {
      setVerifyError(error instanceof ApiError ? error.message : "Could not verify this domain.");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold text-text">Isolation tier</h3>
        {tierError && (
          <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
            {tierError}
          </p>
        )}
        <Select
          label="Tier"
          name="isolation-tier"
          options={TIER_OPTIONS}
          value={tier}
          onChange={(event) => setTier(event.target.value as IsolationTier)}
        />
        {tier === "dedicated_db" && (
          <TextField
            label="Database alias"
            name="db-alias"
            value={dbAlias}
            onChange={(event) => setDbAlias(event.target.value)}
          />
        )}
        <Button onClick={() => void handleSetTier()} disabled={isSettingTier}>
          {isSettingTier ? "Saving…" : "Save isolation tier"}
        </Button>
      </section>

      <section className="flex flex-col gap-3 border-t border-border pt-4">
        <h3 className="text-sm font-semibold text-text">Custom domain</h3>
        {domainError && (
          <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
            {domainError}
          </p>
        )}
        <TextField
          label="Hostname"
          name="hostname"
          placeholder="school.example.com"
          value={hostname}
          onChange={(event) => setHostname(event.target.value)}
        />
        <Button onClick={() => void handleAddDomain()} disabled={isAddingDomain}>
          {isAddingDomain ? "Adding…" : "Add domain"}
        </Button>

        {addedDomain && !verifiedDomain && (
          <div className="rounded-input border border-border bg-surface-muted p-3 text-sm text-text">
            <p>
              Publish a TXT record for <strong>{addedDomain.hostname}</strong> with the value:
            </p>
            <p className="break-all font-mono text-xs">{addedDomain.verification_token}</p>
            <div className="mt-3 flex flex-col gap-2">
              {verifyError && (
                <p role="alert" className="text-sm text-danger">
                  {verifyError}
                </p>
              )}
              <TextField
                label="Resolved TXT record(s)"
                name="resolved-txt-records"
                placeholder="Comma-separated if more than one"
                value={resolvedRecords}
                onChange={(event) => setResolvedRecords(event.target.value)}
              />
              <Button
                variant="outline"
                onClick={() => void handleVerifyDomain()}
                disabled={isVerifying}
              >
                {isVerifying ? "Verifying…" : "Verify domain"}
              </Button>
            </div>
          </div>
        )}
        {verifiedDomain && <p className="text-sm text-success">{verifiedDomain.hostname} verified.</p>}
      </section>
    </div>
  );
}
