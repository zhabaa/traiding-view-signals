(() => {
    const statusEl = document.getElementById("status");
    const symbolEl = document.getElementById("symbol");
    const tfEl = document.getElementById("tf");
    const reloadBtn = document.getElementById("reload");

    const chartEl = document.getElementById("chart");

    function setStatus(text) {
        statusEl.textContent = text;
    }

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return await r.json();
    }

    console.log("LightweightCharts:", LightweightCharts);

    // Chart init
    const chart = LightweightCharts.createChart(chartEl, {
        layout: {background: {type: "solid", color: "#0b0f14"}, textColor: "#d1d4dc"},
        grid: {vertLines: {color: "rgba(42,46,57,0.5)"}, horzLines: {color: "rgba(42,46,57,0.5)"}},
        rightPriceScale: {borderColor: "rgba(42,46,57,0.8)"},
        timeScale: {borderColor: "rgba(42,46,57,0.8)"},
    });

    const candlesSeries = chart.addSeries(LightweightCharts.CandlestickSeries);
    const markers = LightweightCharts.createSeriesMarkers(candlesSeries);


    // Resize
    const ro = new ResizeObserver(() => {
        chart.applyOptions({width: chartEl.clientWidth, height: chartEl.clientHeight});
        chart.timeScale().fitContent();
    });
    ro.observe(chartEl);

    let lastMarkerId = 0;

    async function loadAll() {
        const symbol = symbolEl.value;
        const tf = tfEl.value;

        setStatus("loading candles…");
        const candles = await fetchJSON(`/api/candles?symbol=${encodeURIComponent(symbol)}&tf=${encodeURIComponent(tf)}&limit=500`);
        candlesSeries.setData(candles);
        chart.timeScale().fitContent();

        setStatus("loading markers…");
        const markersResp = await fetchJSON(`/api/markers?symbol=${encodeURIComponent(symbol)}&limit=200`);
        markers.setMarkers(array);
        lastMarkerId = markersResp.last_id || 0;

        setStatus(`ok (markers: ${(markersResp.markers || []).length})`);
    }

    async function pollNewMarkers() {
        const symbol = symbolEl.value;
        try {
            const delta = await fetchJSON(`/api/markers?symbol=${encodeURIComponent(symbol)}&since_id=${lastMarkerId}&limit=200`);
            if (delta.markers && delta.markers.length) {
                // обновим целиком последние 200 (самый простой стабильный способ)
                const full = await fetchJSON(`/api/markers?symbol=${encodeURIComponent(symbol)}&limit=200`);
                markers.setMarkers(full.markers || []);
                lastMarkerId = full.last_id || lastMarkerId;
                setStatus(`updated (markers: ${(full.markers || []).length})`);
            }
        } catch (e) {
            setStatus("poll error");
        }
    }

    reloadBtn.addEventListener("click", loadAll);
    symbolEl.addEventListener("change", loadAll);
    tfEl.addEventListener("change", loadAll);

    loadAll();
    setInterval(pollNewMarkers, 3000);
})();
