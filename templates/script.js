const searchBox = document.getElementById('search-box');
const searchList = document.getElementById('search-list')

async function loadAnime(searchTerm) {
    const url = `https://api.jikan.moe/v4/anime?order_by=score&sort=desc&q=${searchTerm}&sfw&page=1`;
    const res = await fetch(`${url}`);
    const data = await res.json();
    const results = data.data;
    if (res.status === 200) {
        console.log(results);
        displaySearchList(results);
    }
}

function findAnime() {
    let searchTerm = (searchBox.value);
    if (searchTerm.length > 0) {
        loadAnime(searchTerm);
    }
}

function displaySearchList(anime) {
    searchList.innerHTML = " ";
    for (let i = 0; i < anime.length; i++) {
        let animeListItem = document.createElement('div');
        animeListItem.dataset.id = anime[i].mal_id;
        animeListItem.classList.add('search-list-item');
        animePoster = anime[i].images.jpg.small_image_url;
        animeListItem.innerHTML = `
        <div class="search-item-poster">
            <img src="${animePoster}">
        </div>
        <div class="search-item-info">
            <h3>${anime[i].title}</h3>
            <p>${anime[i].score}</p>
            <p>${anime[i].year}</p>
        </div>
        `;
        searchList.appendChild(animeListItem);
    }
}

// const userCardTemplate = document.querySelector("[data-user-template]")
// const userCardContainer = document.querySelector("[data-user-cards-container]")

// fetch("https://api.jikan.moe/v4/top/anime?sfw=true&limit=10")
//     .then(res => res.json())
//     .then(data => {
//         let results = data.data;
//         results.forEach(shows => {
//             const card = userCardTemplate.content.cloneNode(true).children[0];
//             const header = card.querySelector("[data-header]");
//             const body = card.querySelector('[data-body]');
//             header.textContent = shows.title;
//             body.textContent = shows.rank;
//             userCardContainer.append(card)
//         })
//     });
