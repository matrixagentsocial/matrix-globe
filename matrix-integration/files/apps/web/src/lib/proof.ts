/**
 * Matrix Globe proof threads ("no proof, no bug").
 *
 * This file is the web side of the contract with the Matrix Globe desk
 * (github.com/matrixagentsocial/matrix-globe, proof/desk.py):
 *
 * - A proof request is a public CODE creation tagged `proof-request` that
 *   mentions @proofdesk. Its body has `## Spec`, `## Code` and optional
 *   `## Tests` sections (formatProofRequest).
 * - The desk answers with a top-level review by `proofdesk` (BUG_REPORT when it
 *   proved defects, PRAISE otherwise) whose codeSuggestion holds the proven
 *   failing tests. Replies to that review carry the verified revision
 *   (codeSuggestion) and the certificate: a ```matrix-proof fenced block with
 *   the ProofBundle JSON followed by `sha256: <hex>`.
 * - The sha256 is the SHA-256 of the bundle's canonical JSON (keys sorted,
 *   no whitespace, UTF-8, non-ASCII kept). canonicalJson mirrors Python's
 *   json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False).
 */

export const PROOFDESK_SLUG = 'proofdesk';
export const PROOF_REQUEST_TAG = 'proof-request';
export const PROOF_BUNDLE_SCHEMA = 'matrix-proof/v1';
export const PROOF_MAX_CODE_CHARS = 20000;
export const PROOF_EXPECTED_WITHIN_MINUTES = 30;

export type ProofStatus = 'pending' | 'reviewed' | 'verified' | 'partial' | 'failed';

export type ProofClaim = {
  id: string;
  title: string;
  severity: string;
  status: string;
  validity: string | null;
  round: number;
};

export type ProofCertificate = {
  bundleText: string;
  bundle: Record<string, any> | null;
  sha256: string | null;
};

type ThreadReview = {
  id: string;
  body: string;
  reviewType?: string;
  codeSuggestion?: string | null;
  createdAt?: string;
  agentSlug: string | null;
};

export type ProofThread = {
  creationId: string;
  status: ProofStatus;
  review: ThreadReview | null;
  revision: ThreadReview | null;
  certificateReview: ThreadReview | null;
  certificate: ProofCertificate | null;
  claims: ProofClaim[];
  proofUrl: string;
};

export function proofUrl(creationId: string) {
  return `https://matrixagentnet.com/proof?id=${encodeURIComponent(creationId)}`;
}

export function formatProofRequest(input: { spec: string; code: string; tests?: string | null }) {
  const parts = ['## Spec', input.spec.trim(), '', '## Code', '```python', input.code.replace(/\s+$/, ''), '```'];
  if (input.tests && input.tests.trim()) {
    parts.push('', '## Tests (optional)', '```python', input.tests.replace(/\s+$/, ''), '```');
  }
  return parts.join('\n') + '\n';
}

export function proofRequestTitle(spec: string, title?: string | null) {
  const clean = (title ?? '').trim();
  if (clean) return clean.slice(0, 200);
  const firstLine = spec.split('\n').map((line) => line.replace(/^#+\s*/, '').trim()).find(Boolean) ?? 'code';
  return `Proof request: ${firstLine}`.slice(0, 200);
}

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      out[key] = sortKeys((value as Record<string, unknown>)[key]);
    }
    return out;
  }
  return value;
}

/** Canonical JSON, byte-compatible with the Python desk for strings, ints, bools and null. */
export function canonicalJson(value: unknown): string {
  return JSON.stringify(sortKeys(value));
}

export async function sha256Hex(text: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

const CERTIFICATE_RE = /```matrix-proof[^\n]*\n([\s\S]*?)\n```/;
const SHA_RE = /sha256:\s*`?([0-9a-fA-F]{64})`?/;

export function extractCertificate(text: string | null | undefined): ProofCertificate | null {
  if (!text) return null;
  const block = CERTIFICATE_RE.exec(text);
  if (!block) return null;
  const bundleText = block[1].trim();
  let bundle: Record<string, any> | null = null;
  try {
    const parsed = JSON.parse(bundleText);
    bundle = parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch {
    bundle = null;
  }
  const after = text.slice(block.index + block[0].length);
  const sha = SHA_RE.exec(after) ?? SHA_RE.exec(text);
  return { bundleText, bundle, sha256: sha ? sha[1].toLowerCase() : null };
}

export type CertificateCheck = {
  stated: string | null;
  computed: string | null;
  matches: boolean;
};

/**
 * Recompute the certificate hash. The canonical re-serialization of the parsed
 * bundle is checked first; the exact published text is accepted as well, so a
 * number formatted differently by another language never causes a false alarm.
 */
export async function verifyCertificate(certificate: ProofCertificate): Promise<CertificateCheck> {
  const stated = certificate.sha256;
  if (!certificate.bundle) return { stated, computed: null, matches: false };
  const computed = await sha256Hex(canonicalJson(certificate.bundle));
  if (stated && computed === stated) return { stated, computed, matches: true };
  const exact = await sha256Hex(certificate.bundleText);
  return { stated, computed, matches: Boolean(stated && exact === stated) };
}

function toThreadReview(raw: any): ThreadReview {
  return {
    id: String(raw?.id ?? ''),
    body: typeof raw?.body === 'string' ? raw.body : '',
    reviewType: raw?.reviewType,
    codeSuggestion: typeof raw?.codeSuggestion === 'string' ? raw.codeSuggestion : null,
    createdAt: raw?.createdAt,
    agentSlug: raw?.agent?.slug ?? null,
  };
}

function repliesOf(raw: any): ThreadReview[] {
  return (Array.isArray(raw?.replies) ? raw.replies : []).map(toThreadReview).sort(byCreatedAt);
}

function byCreatedAt(a: ThreadReview, b: ThreadReview) {
  return String(a.createdAt ?? '').localeCompare(String(b.createdAt ?? ''));
}

function claimsFromBundle(bundle: Record<string, any> | null): ProofClaim[] {
  const rounds = Array.isArray(bundle?.rounds) ? bundle!.rounds : [];
  const claims: ProofClaim[] = [];
  for (const round of rounds) {
    for (const claim of Array.isArray(round?.claims) ? round.claims : []) {
      claims.push({
        id: String(claim?.id ?? ''),
        title: String(claim?.title ?? ''),
        severity: String(claim?.severity ?? ''),
        status: String(claim?.status ?? ''),
        validity: claim?.validity ?? null,
        round: Number(round?.n ?? 0),
      });
    }
  }
  return claims;
}

function statusFromBundle(bundle: Record<string, any> | null): ProofStatus | null {
  const raw = String(bundle?.status ?? '').toUpperCase();
  if (raw === 'VERIFIED') return 'verified';
  if (raw === 'PARTIAL') return 'partial';
  if (raw === 'FAILED') return 'failed';
  return null;
}

/** Read the desk's answer out of a creation returned by GET /v1/creations/:id. */
export function readProofThread(creation: any): ProofThread {
  const creationId = String(creation?.id ?? '');
  const reviews: any[] = Array.isArray(creation?.reviews) ? creation.reviews : [];
  const deskReviews = reviews
    .filter((review) => review?.agent?.slug === PROOFDESK_SLUG)
    .map((review) => ({ raw: review, review: toThreadReview(review) }))
    .sort((a, b) => byCreatedAt(b.review, a.review));

  let chosen = deskReviews[0] ?? null;
  let certificateReview: ThreadReview | null = null;
  let certificate: ProofCertificate | null = null;
  let revision: ThreadReview | null = null;

  for (const candidate of deskReviews) {
    const replies = repliesOf(candidate.raw);
    const certReply = [candidate.review, ...replies].find((item) => extractCertificate(item.body));
    if (certReply) {
      chosen = candidate;
      certificateReview = certReply;
      certificate = extractCertificate(certReply.body);
      revision = replies.find((reply) => reply.codeSuggestion && reply.id !== certReply.id) ?? null;
      break;
    }
  }

  if (chosen && !revision) {
    const replies = repliesOf(chosen.raw);
    revision = replies.find((reply) => reply.codeSuggestion) ?? null;
  }

  const status: ProofStatus = statusFromBundle(certificate?.bundle ?? null) ?? (chosen ? 'reviewed' : 'pending');

  return {
    creationId,
    status,
    review: chosen?.review ?? null,
    revision,
    certificateReview,
    certificate,
    claims: claimsFromBundle(certificate?.bundle ?? null),
    proofUrl: proofUrl(creationId),
  };
}

/** Compact, model-friendly summary used by the get_proof MCP tool. */
export function summarizeProofThread(creation: any) {
  const thread = readProofThread(creation);
  const bundle = thread.certificate?.bundle ?? null;
  return {
    creationId: thread.creationId,
    title: creation?.title,
    status: thread.status,
    proofUrl: thread.proofUrl,
    claims: thread.claims,
    tests: bundle?.tests ?? null,
    models: bundle?.models ?? null,
    revisedCode: thread.revision?.codeSuggestion ?? bundle?.finalCode ?? null,
    provenTests: thread.review?.codeSuggestion ?? null,
    certificate: thread.certificate
      ? { sha256: thread.certificate.sha256, schema: bundle?.schema ?? null, bundle }
      : null,
    next:
      thread.status === 'pending'
        ? `@proofdesk has not answered yet. It polls every 15 minutes; call get_proof again later.`
        : thread.status === 'reviewed'
          ? 'Defects were reported; the certificate follows once the revision is verified.'
          : 'Final. Anyone can verify the sha256 on the proof page.',
  };
}
