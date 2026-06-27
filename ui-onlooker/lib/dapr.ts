// Server-only Dapr pub/sub publisher. The UI publishes events (e.g.
// document.uploaded) to its own Dapr sidecar; the pipeline microservices react.

export async function publish(topic: string, data: unknown): Promise<void> {
  const port = process.env.DAPR_HTTP_PORT || "3500";
  const pubsub = process.env.PUBSUB_NAME || "pubsub";
  const url = `http://localhost:${port}/v1.0/publish/${pubsub}/${topic}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`dapr publish ${topic} failed: ${res.status} ${await res.text()}`);
  }
}
