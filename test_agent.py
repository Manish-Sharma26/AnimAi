from agent.orchestrator import run_agent

# Test prompt — change this to anything you want!
query = "Animate neural network training with a loss curve and weight updates"

result = run_agent(query)

if result["status"] == "success":
    print(f"\n🎉 Open this file to watch your animation:")
    print(f"   {result['video_path']}")
else:
    print(f"\n❌ Failed after {result['attempts']} attempts")
    print(f"Error: {result['error'][:300]}")