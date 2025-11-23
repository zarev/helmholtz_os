import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createServer,
  echoMarkdownTool,
  helloPrompt,
  sayHelloTool,
  serverInfoResource,
} from './server.js';

const textContent = (content) => content?.find((item) => item.type === 'text');

test('say_hello tool returns a greeting with sparkle', async () => {
  const result = await sayHelloTool({ name: 'Ada' });
  const text = textContent(result.content)?.text;
  assert.equal(text, 'Hello, Ada! ✨');
});

test('echo_markdown tool wraps text in a fenced code block', async () => {
  const sample = 'echo me';
  const result = await echoMarkdownTool({ text: sample });
  const text = textContent(result.content)?.text;
  assert.ok(text?.includes('```'));
  assert.ok(text?.includes(sample));
});

test('server-info resource returns static description', async () => {
  const resource = await serverInfoResource();
  assert.equal(resource.contents[0].uri, 'memory:helmholtz-mcp/info');
  assert.match(
    resource.contents[0].text,
    /say_hello, echo_markdown/,
    'Resource text should mention available tools'
  );
});

test('hello_prompt builds a single user message with tone defaulting to friendly', async () => {
  const prompt = await helloPrompt({ name: 'Lin', tone: undefined });
  assert.equal(prompt.messages.length, 1);
  const [message] = prompt.messages;
  assert.equal(message.role, 'user');
  assert.ok(message.content.text.includes('Lin'));
  assert.ok(message.content.text.includes('friendly'));
});

test('createServer registers all primitives without throwing', () => {
  assert.doesNotThrow(() => {
    const server = createServer();
    assert.ok(server);
  });
});
