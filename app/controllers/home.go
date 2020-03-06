package controllers

import (
	"github.com/DCsunset/THUAI-DefenseOfSky/app/globals"
	"github.com/DCsunset/THUAI-DefenseOfSky/app/models"

	"fmt"
	"net/http"
)

// Routed to /
func rootHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "This is the home page!")
}


// add type for choose Organizer or Superuser
func fakeDatabaseHandler(w http.ResponseWriter, r *http.Request) {
	s := r.PostFormValue("handle")
	p := r.PostFormValue("password")
	k := r.PostFormValue("key")
	t := r.PostFormValue("type")
	config := globals.Config()
	if k != config.JudgeSigKey {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{}")
	} else {
		if(t=="o"){
			models.CreateOrganizer(s, p)
			// models.FakeDatabase()
			fmt.Fprintf(w, "Fake User(Organizer) Created\n")
		}else if(t=="s"){
			models.CreateSuperUser(s,p)
			fmt.Fprintf(w, "Fake User(SuperUser) Created\n")
		}
	}
}

func fakeMatchesHandler(w http.ResponseWriter, r *http.Request) {
	models.FakeMatches()
	fmt.Fprintf(w, "Matches automagically run\n")
}

func init() {
	registerRouterFunc("/", rootHandler)
	registerRouterFunc("/fake", fakeDatabaseHandler, "POST")
	//registerRouterFunc("/fake_matches", fakeMatchesHandler, "POST")
}
