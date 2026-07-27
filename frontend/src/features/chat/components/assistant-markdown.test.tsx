// @vitest-environment jsdom

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { AssistantMarkdown } from './assistant-markdown'

describe('AssistantMarkdown', () => {
  it('renders common Gemini Markdown and GFM structures', () => {
    const { container } = render(
      <AssistantMarkdown
        content={[
          '# Launch plan',
          '',
          '- Build',
          '- Test',
          '',
          '| Stage | Owner |',
          '| --- | --- |',
          '| QA | Amir |',
          '',
          '[Docs](https://example.com)',
          '',
          '~~Removed~~',
        ].join('\n')}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Launch plan' })).toBeTruthy()
    expect(screen.getByRole('list')).toBeTruthy()
    expect(screen.getByRole('table')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Docs' }).getAttribute('rel')).toBe(
      'noopener noreferrer nofollow',
    )
    expect(container.querySelector('del')?.textContent).toBe('Removed')
  })

  it('does not render raw HTML or remote images', () => {
    const { container } = render(
      <AssistantMarkdown
        content={'<script>alert("unsafe")</script>\n\n![tracking](https://example.com/pixel.png)'}
      />,
    )

    expect(container.querySelector('script')).toBeNull()
    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByText('Image omitted: tracking')).toBeTruthy()
  })

  it('renders fenced code with a language label and copy control', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })
    render(
      <AssistantMarkdown content={'```typescript\nconst ready = true\n```'} />,
    )

    expect(screen.getByText('typescript')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Copy code' }))

    expect(writeText).toHaveBeenCalledWith('const ready = true')
    expect(await screen.findByText('Copied')).toBeTruthy()
  })

  it('shows a generation cursor while content is streaming', () => {
    render(<AssistantMarkdown content="Partial **answer" isStreaming />)

    expect(screen.getByLabelText('Generating')).toBeTruthy()
  })
})
