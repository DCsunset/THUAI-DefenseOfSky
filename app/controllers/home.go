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

func fakeDatabaseHandler(w http.ResponseWriter, r *http.Request) {
	s := r.PostFormValue("handle")
	p := r.PostFormValue("password")
	k := r.PostFormValue("key")
	config := globals.Config()
	if k != config.JudgeSigKey {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{}")
	} else {
		models.CreateOrganizer(s, p)
		// models.FakeDatabase()
		fmt.Fprintf(w, "Fake User Created\n")
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
