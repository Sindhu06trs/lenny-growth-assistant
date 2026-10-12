import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { cleanMarkdownContent } from '../src/services/markdown.ts';

describe('Artifact Viewer Markdown & Content Cleaner Suite', () => {
  it('strips duplicate leading ATX title and underline when matching artifact title', () => {
    const raw = `# The Leaky Bucket Paradox: Why Top-of-Funnel Fixes Won't Solve a Product-Market Fit Issue
============================================================

As a startup founder, you've likely encountered the elusive concept of product-market fit.

## The Root Cause of the Problem
Product-market fit occurs when your product meets the needs of customers.`;

    const title = "The Leaky Bucket Paradox: Why Top-of-Funnel Fixes Won't Solve a Product-Market Fit Issue";
    const cleaned = cleanMarkdownContent(raw, title);

    // Title should be stripped from content
    assert.doesNotMatch(cleaned, /^# The Leaky Bucket Paradox/);
    // Underline should not appear as plain text at top
    assert.doesNotMatch(cleaned, /^={3,}/);
    // Body should start cleanly
    assert.match(cleaned, /^As a startup founder/);
    // Legitimate headings must be preserved
    assert.match(cleaned, /## The Root Cause of the Problem/);
  });

  it('strips duplicate leading setext title and equals underline', () => {
    const raw = `Customer Retention Framework
=============================

Retention is the bedrock of compound growth.

## Core Metrics
- D1 Retention
- D30 Retention`;

    const title = 'Customer Retention Framework';
    const cleaned = cleanMarkdownContent(raw, title);

    assert.doesNotMatch(cleaned, /^Customer Retention Framework/);
    assert.doesNotMatch(cleaned, /^={3,}/);
    assert.match(cleaned, /^Retention is the bedrock/);
    assert.match(cleaned, /## Core Metrics/);
  });

  it('normalizes standalone repeated equals signs into markdown horizontal rules (---)', () => {
    const raw = `## Section 1
First paragraph content.

============================================================

## Section 2
Second paragraph content.`;

    const cleaned = cleanMarkdownContent(raw, 'My Guide');

    // Section 1 must be preserved
    assert.match(cleaned, /## Section 1/);
    // Repeated equals signs must be transformed to markdown hr
    assert.doesNotMatch(cleaned, /={3,}/);
    assert.match(cleaned, /---\n\n## Section 2/);
  });

  it('preserves legitimate headings, paragraphs, lists, links, and citations', () => {
    const raw = `# The Core Thesis

Fix retention before pouring money into acquisition.

## Verified Sources & Citations
* [Brian Chesky on Founder Mode](https://youtube.com/watch?v=123) (Timestamp: 12:45)
* [Lenny's Newsletter: Lean Startup](https://lennys.blog)

### Tactical Checklist
1. Audit onboarding friction.
2. Measure time-to-value (TTV).
3. Establish habit loops.`;

    const cleaned = cleanMarkdownContent(raw, 'The Core Thesis');

    assert.doesNotMatch(cleaned, /^# The Core Thesis/);
    assert.match(cleaned, /^Fix retention before pouring money into acquisition\./);
    assert.match(cleaned, /## Verified Sources & Citations/);
    assert.match(cleaned, /\* \[Brian Chesky on Founder Mode\]/);
    assert.match(cleaned, /### Tactical Checklist/);
    assert.match(cleaned, /1\. Audit onboarding friction\./);
  });

  it('does not delete legitimate headings when title does not match first line', () => {
    const raw = `## Introduction
This is an introductory note without leading H1.

## Deep Dive
Detailed analysis.`;

    const cleaned = cleanMarkdownContent(raw, 'Different Title');

    // Heading 2 at the top should NOT be stripped because it is not an H1 and doesn't match the title
    assert.match(cleaned, /^## Introduction/);
    assert.match(cleaned, /## Deep Dive/);
  });
});
