$(document).ready(function() {
    let currentPage = 1;
    let pageSize = 20;
    let loading = false;

    function loadMore() {
        if (loading) return;
        loading = true;

        currentPage++;
        $.get(`/load_more/${currentPage}`, function(data) {
            let animeGrid = $(".anime-grid");
            // for (let i = 0; i < data.length; i++) {
            //     let anime = data[i];
            //     let animeHtml = `<div class="anime-card">${anime.title}</div>`;
            //     animeGrid.append(animeHtml);
            // }
            let anime = data[0];
            let animeHtml = `<div class="anime-card">${anime.title}</div>`;
            animeGrid.push(animeHtml);


            loading = false;
        });
    }

    $("#load-more-button").click(loadMore)
})
