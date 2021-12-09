//JS code for popup
//const baseurl = 'http://127.0.0.1:5000' //local
const baseurl = 'https://33sd.ngrok.io' //hosted

fetchTconst()

//fetch the tconst from IMDB page
function fetchTconst(){
  chrome.tabs.query({active: true, lastFocusedWindow: true}, tabs => {
    try{
      let u = tabs[0].url;
      let url = new URL(u);
      let tconst = url.pathname.split('/')[2];
      if(!tconst.includes('tt')){
        throw 'not a valid tconst'
      }
      getBaseMovie(tconst)
    }
    catch{
      show_error()
    }
  });
}

//get the base movie info
function getBaseMovie(tconst){
  const http = new XMLHttpRequest();
  const url=`${baseurl}/movie?tconst=${tconst}`;
  http.open("GET", url);
  http.send();
  http.onreadystatechange=(e)=>{
    const obj = JSON.parse(http.responseText)
    document.getElementById("BaseMovie").innerText = obj.title;
    getSimilarMovie(tconst)
  } 
}

//get the similar movie info
function getSimilarMovie(tconst){
  const http = new XMLHttpRequest();
  const url=`${baseurl}/similar?tconst=${tconst}&limit=20`;
  http.open("GET", url);
  http.send();
  http.onreadystatechange=(e)=>{
    const obj = JSON.parse(http.responseText)
    buildMovieTable(obj.all)
  }
}

//build the similar movie table
function buildMovieTable(movieArr){
  var tot = '';
  for(let i=0; i<movieArr.length; i++){
    let movie = movieArr[i]
    let html = `<div class="movie"><img class="movie-img" src="${movie.poster}">`
    html += `<a class="movie-title" href="https://www.imdb.com/title/${movie.tconst}" target="_blank"><b>${movie.title}</b></a>`
    html += `<h3 class="movie-stars"><span class="yellow">⭐</span> ${movie.rating}/10</h3>`
    html += `</div>`
    tot += html
  }
  document.getElementById("Movies").innerHTML = tot;
  //hide the loader and show movies
  document.getElementById("Loading").style.display = "none";
  document.getElementById("Content").style.display = "block";
}

//show error screen
function show_error(){
  document.getElementById("Loading").style.display = "none";
  document.getElementById("Error").style.display = "block";
}