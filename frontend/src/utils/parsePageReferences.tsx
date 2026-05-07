import React from 'react'
import { FileText } from 'lucide-react'

/**
 * Detect page numbers in text using various common patterns
 * Matches: "page 8", "Page 12", "pg. 5", "p. 23"
 */
export function detectPageReferences(text: string): number[] {
    if (!text) return []

    const pageReferencePattern = /\b(?:page|Page|PAGE|pg\.|Pg\.|p\.|P\.)\s*(\d+)\b/gi
    const matches = text.matchAll(pageReferencePattern)

    const pageNumbers = new Set<number>()
    for (const match of matches) {
        const pageNum = parseInt(match[1], 10)
        if (pageNum > 0) {
            pageNumbers.add(pageNum)
        }
    }

    return Array.from(pageNumbers).sort((a, b) => a - b)
}

/**
 * Extract page number from a pageLocation string like "Page 15, Section 3.2"
 */
export function extractPageNumber(pageLocation: string): number | null {
    if (!pageLocation) return null
    const match = pageLocation.match(/\b(?:page|Page|PAGE|pg\.|Pg\.|p\.|P\.)\s*(\d+)\b/i)
    return match ? parseInt(match[1], 10) : null
}

/**
 * Transform text to include clickable page references
 * Returns JSX with clickable links for page numbers
 * @param text - The text containing page references
 * @param onPageClick - Callback when page is clicked (page, highlightText?)
 * @param highlightText - Optional text to pass for highlighting when clicked
 */
export function createClickablePageLinks(
    text: string,
    onPageClick: (page: number, highlightText?: string) => void,
    highlightText?: string
): React.ReactNode {
    if (!text) return text

    const pageReferencePattern = /\b(page|Page|PAGE|pg\.|Pg\.|p\.|P\.)\s*(\d+)\b/gi
    const parts: (string | React.ReactNode)[] = []
    let lastIndex = 0

    const matches = Array.from(text.matchAll(pageReferencePattern))

    matches.forEach((match, idx) => {
        const matchStart = match.index!
        const matchEnd = matchStart + match[0].length

        // Add text before the match
        if (matchStart > lastIndex) {
            parts.push(text.substring(lastIndex, matchStart))
        }

        // Add clickable page reference
        const pageNum = parseInt(match[2], 10)
        parts.push(
            <button
                key={`page-ref-${idx}-${pageNum}`}
                onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onPageClick(pageNum, highlightText)
                }}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline cursor-pointer font-medium transition-colors"
                title={highlightText ? `Jump to page ${pageNum} and highlight evidence` : `Jump to page ${pageNum}`}
            >
                {match[0]}
            </button>
        )

        lastIndex = matchEnd
    })

    // Add remaining text after last match
    if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex))
    }

    return parts.length > 0 ? <>{parts}</> : text
}

/**
 * Create a clickable evidence page link that highlights the quote when clicked
 * @param evidence - Evidence object with quote and pageLocation
 * @param onPageClick - Callback when clicked (page, highlightText)
 * @param idx - Index for key generation
 */
export function createEvidencePageLink(
    evidence: { quote?: string; pageLocation?: string },
    onPageClick: (page: number, highlightText?: string) => void,
    idx: number = 0
): React.ReactNode {
    if (!evidence.pageLocation) return null

    const pageNum = extractPageNumber(evidence.pageLocation)
    if (!pageNum) {
        // If we can't extract page number, just display the location as text
        return <span className="text-xs text-muted-foreground">{evidence.pageLocation}</span>
    }

    return (
        <button
            key={`evidence-page-ref-${idx}-${pageNum}`}
            onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('🔗 Evidence link clicked:', {
                    pageNum,
                    pageLocation: evidence.pageLocation,
                    quote: evidence.quote,
                    quoteLength: evidence.quote?.length
                })
                onPageClick(pageNum, evidence.quote)
            }}
            className="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline cursor-pointer font-medium transition-colors text-xs"
            title={evidence.quote ? `Go to ${evidence.pageLocation} and highlight evidence` : `Go to ${evidence.pageLocation}`}
        >
            <FileText className="h-3 w-3" />
            {evidence.pageLocation}
        </button>
    )
}

/**
 * Recursively parse JSON object and extract all page references
 */
export function extractAllPageReferences(data: any): number[] {
    const pageNumbers = new Set<number>()

    function traverse(obj: any) {
        if (typeof obj === 'string') {
            const refs = detectPageReferences(obj)
            refs.forEach(num => pageNumbers.add(num))
        } else if (Array.isArray(obj)) {
            obj.forEach(item => traverse(item))
        } else if (obj && typeof obj === 'object') {
            Object.values(obj).forEach(value => traverse(value))
        }
    }

    traverse(data)
    return Array.from(pageNumbers).sort((a, b) => a - b)
}
