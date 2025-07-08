const res = fetch('https://api.nuwaapi.com/v1/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 5
    })}
)

const fn = async () => {
    const res = await fetch('https://api.nuwaapi.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 5
        })
    })
    const data = await res.json()
    console.log(data)
}

fn()

