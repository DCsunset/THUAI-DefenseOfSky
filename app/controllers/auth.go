package controllers

import (
	"github.com/kawa-yoiko/botany/app/globals"
	"github.com/kawa-yoiko/botany/app/models"

	"bytes"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/gorilla/mux"
	"io"
	"mime"
	"net/http"
	"strings"
)

// Returns a User struct
func middlewareAuthRetrieve(w http.ResponseWriter, r *http.Request) models.User {
	session, err := globals.SessionStore.Get(r, "auth")
	if err != nil {
		panic(err)
	}

	id, ok := session.Values["uid"].(int32)
	if !ok {
		return models.User{Id: -1}
	}

	u := models.User{Id: id}
	if err := u.ReadById(); err != nil {
		if err == sql.ErrNoRows {
			return models.User{Id: -1}
		} else {
			panic(err)
		}
	}
	return u
}

func middlewareAuthGrant(w http.ResponseWriter, r *http.Request, uid int32) {
	session, err := globals.SessionStore.Get(r, "auth")
	if err != nil {
		panic(err)
	}

	session.Values["uid"] = uid
	err = session.Save(r, w)
	if err != nil {
		panic(err)
	}
}

func middlewareCaptchaVerify(w http.ResponseWriter, r *http.Request) bool {
	captchaKey := r.PostFormValue("captcha_key")
	captchaValue := r.PostFormValue("captcha_value")
	return globals.CaptchaVerfiy(captchaKey, captchaValue)
}

func middlewareUserEditVerify(w http.ResponseWriter, r *http.Request) models.User {
	u := middlewareAuthRetrieve(w, r)
	if u.Id == -1 {
		w.WriteHeader(401)
		return u
	}

	// The user being referred to
	ur := models.User{Handle: mux.Vars(r)["handle"]}
	if u.Handle != ur.Handle && u.Privilege != models.UserPrivilegeSuperuser {
		// Not superuser and handle does match logged-in user
		w.WriteHeader(403)
		return models.User{Id: -1}
	}

	if err := ur.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			w.WriteHeader(404)
			return models.User{Id: -1}
		} else {
			panic(err)
		}
	}

	return ur
}

// Returns file name extension and a buffer of contents
func middlewareMultipartFormFile(r *http.Request) (error, string, bytes.Buffer) {
	var buf bytes.Buffer

	// 1 MiB maximum
	// TODO: Allow changing this in configuration
	r.ParseMultipartForm(1 << 20)
	f, h, err := r.FormFile("file")
	if err != nil {
		return err, "", buf
	}
	defer f.Close()

	nameParts := strings.Split(h.Filename, ".")
	extension := ""
	if len(nameParts) >= 2 {
		extension = nameParts[len(nameParts)-1]
	}
	io.Copy(&buf, f)
	return nil, extension, buf
}

// curl http://localhost:3434/signup -i -d "handle=abc&password=qwq&email=gamma@example.com&nickname=ABC&captcha_key=...&captcha_value=..."
func signupHandler(w http.ResponseWriter, r *http.Request) {
	if !middlewareCaptchaVerify(w, r) {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\": [3]}")
		return
	}

	s := r.PostFormValue("handle")
	p := r.PostFormValue("password")
	email := r.PostFormValue("email")
	nickname := r.PostFormValue("nickname")

	u := models.User{}
	u.Handle = s
	u.Email = email

	if !u.EmailCheck() {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\": [-1]}")
		return
	}

	// check whether a user with the same handle or email is existing
	userExist := true
	if err := u.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			userExist = false
		} else {
			panic(err)
		}
	}
	if userExist {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\": [1]}")
		return
	}
	userExist = true
	if err := u.ReadByEmail(); err != nil {
		if err == sql.ErrNoRows {
			userExist = false
		} else {
			panic(err)
		}
	}
	if userExist {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\": [2]}")
		return
	}

	u.Password = p
	u.Nickname = nickname
	if err := u.Create(); err != nil {
		panic(err)
	}

	fmt.Fprintf(w, "{\"err\": []}")
}

// curl http://localhost:3434/login -i -d "handle=abc&password=qwq"
func loginHandler(w http.ResponseWriter, r *http.Request) {
	s := r.PostFormValue("handle")
	p := r.PostFormValue("password")

	// TODO: Support logging in with e-mail
	u := models.User{}
	u.Handle = s

	ok := true

	if err := u.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			ok = false
		} else {
			panic(err)
		}
	}

	if ok && !u.VerifyPassword(p) {
		ok = false
	}

	if !ok {
		u = models.User{}
		u.Email = s
		if err := u.ReadByEmail(); err != nil {
			if err != sql.ErrNoRows {
				panic(err)
			}
		}
		if u.VerifyPassword(p) {
			ok = true
		}
	}

	if ok {
		middlewareAuthGrant(w, r, u.Id)
		w.WriteHeader(200)
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		enc.Encode(u.Representation())
	} else {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{}")
	}
}

// curl http://localhost:3434/logout -i -H "Cookie: auth=..." -d ""
func logoutHandler(w http.ResponseWriter, r *http.Request) {
	session, err := globals.SessionStore.Get(r, "auth")
	if err != nil {
		panic(err)
	}

	// Delete session
	session.Options.MaxAge = -1
	err = session.Save(r, w)
	if err != nil {
		panic(err)
	}
}

// curl http://localhost:3434/whoami -i -H "Cookie: auth=..."
func whoAmIHandler(w http.ResponseWriter, r *http.Request) {
	u := middlewareAuthRetrieve(w, r)
	if u.Id == -1 {
		w.WriteHeader(400)
	} else {
		w.WriteHeader(200)
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		enc.Encode(u.ShortRepresentation())
	}
}

func captchaGetHandler(w http.ResponseWriter, r *http.Request) {
	key, img := globals.CaptchaCreate()
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	enc.Encode(map[string]string{
		"key": key,
		"img": img,
	})
}

func profileHandler(w http.ResponseWriter, r *http.Request) {
	u := models.User{Handle: mux.Vars(r)["handle"]}
	if err := u.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			// No such user
			w.WriteHeader(404)
			return
		} else {
			panic(err)
		}
	}

	limit, offset := parsePagination(w, r)
	if limit == -1 && offset == -1 {
		w.WriteHeader(400)
		return
	}

	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	contests, _ := u.AllContests()
	matches, total, _ := u.MatchesPagination(limit, offset)
	enc.Encode(map[string]interface{}{
		"user":          u.Representation(),
		"contests":      contests,
		"matches":       matches,
		"total_matches": total,
	})
}

func profileEditHandler(w http.ResponseWriter, r *http.Request) {
	user := middlewareUserEditVerify(w, r)

	user.Email = r.PostFormValue("email")
	user.Nickname = r.PostFormValue("nickname")
	user.Bio = r.PostFormValue("bio")

	if !user.EmailCheck() {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\": [-1]}")
		return
	}

	// Check if the mail is available
	e := models.User{Email: user.Email}
	err := e.ReadByEmail()
	if err != nil && err != sql.ErrNoRows {
		// this user is not existed but the error is not no rows
		panic(err)
	} else if err == nil && e.Id != user.Id {
		// this user is existed and it is not the user whose info is being edited
		w.WriteHeader(400)
		fmt.Fprintf(w, "{\"err\":[1]}")
		return
	}

	if err := user.Update(); err != nil {
		panic(err)
	}

	w.WriteHeader(200)
	fmt.Fprintf(w, "{}")
}

func passwordEditHandler(w http.ResponseWriter, r *http.Request) {
	user := middlewareUserEditVerify(w, r)
	if user.Id == -1 {
		return
	}

	old := r.PostFormValue("old")
	new := r.PostFormValue("new")

	// the old password is wrong
	if !user.VerifyPassword(old) {
		w.WriteHeader(400)
		fmt.Fprintf(w, "{}")
		return
	}

	user.Password = new
	if err := user.UpdatePassword(); err != nil {
		panic(err)
	}
	w.WriteHeader(200)
	fmt.Fprintf(w, "{}")
}

func avatarHandler(w http.ResponseWriter, r *http.Request) {
	u := models.User{Handle: mux.Vars(r)["handle"]}
	if err := u.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			w.WriteHeader(404)
			return
		} else {
			panic(err)
		}
	}

	f, err := u.LoadAvatar()
	if err != nil {
		panic(err)
	}

	if f.Id == -1 {
		f = globals.DefaultAvatar
	}

	w.Header().Set("Content-Type", f.Type)
	w.Write(f.Content)
}

func avatarUploadHandler(w http.ResponseWriter, r *http.Request) {
	u := middlewareUserEditVerify(w, r)
	if u.Id == -1 {
		return
	}

	err, ext, buf := middlewareMultipartFormFile(r)
	if errors.Is(err, http.ErrMissingFile) {
		// No such file
		w.WriteHeader(400)
		return
	} else if err != nil {
		panic(err)
	}

	mimeType := mime.TypeByExtension("." + ext)
	if !strings.HasPrefix(mimeType, "image/") {
		// Unsupported file extension
		w.WriteHeader(400)
		return
	}

	f, err := u.LoadAvatar()
	if err != nil {
		panic(err)
	}
	f.Type = mimeType
	f.Content = buf.Bytes()

	if f.Id == -1 {
		err = f.Create()
		if err == nil {
			u.Avatar = f.Id
			err = u.UpdateAvatar()
		}
	} else {
		err = f.Update()
	}
	if err != nil {
		panic(err)
	}
}

// 赋予或撤回主办权限
func promoteHandler(w http.ResponseWriter, r *http.Request) {
	u := middlewareAuthRetrieve(w, r)
	if u.Id == -1 {
		w.WriteHeader(401)
		return
	}

	if u.Privilege != models.UserPrivilegeSuperuser {
		// this user is not superuser
		w.WriteHeader(403)
		fmt.Fprintf(w, "{}")
		return
	}

	user := models.User{Handle: mux.Vars(r)["handle"]}
	if err := user.ReadByHandle(); err != nil {
		if err == sql.ErrNoRows {
			w.WriteHeader(404)
			return
		} else {
			panic(err)
		}
	}

	set := r.PostFormValue("set")
	if set == "true" {
		user.Privilege = models.UserPrivilegeOrganizer
	} else if set == "false" && user.Privilege == models.UserPrivilegeOrganizer {
		user.Privilege = models.UserPrivilegeNormal
	}

	if err := user.Update(); err != nil {
		panic(err)
	}
	w.WriteHeader(200)
	fmt.Fprintf(w, "{}")
}

func userSearchHandler(w http.ResponseWriter, r *http.Request) {
	h := mux.Vars(r)["handle"]
	us, err := models.UserSearchByHandle(h)
	if err != nil {
		panic(err)
	}

	w.Write([]byte("["))
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	for i, u := range us {
		if i != 0 {
			w.Write([]byte(","))
		}
		enc.Encode(u.ShortRepresentation())
	}
	w.Write([]byte("]\n"))
}

func init() {
	registerRouterFunc("/signup", signupHandler, "POST")
	registerRouterFunc("/login", loginHandler, "POST")
	registerRouterFunc("/logout", logoutHandler, "POST")
	registerRouterFunc("/whoami", whoAmIHandler, "GET")

	registerRouterFunc("/captcha", captchaGetHandler, "GET")

	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/profile", profileHandler, "GET")
	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/profile/edit", profileEditHandler, "POST")
	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/password", passwordEditHandler, "POST")
	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/avatar", avatarHandler, "GET")
	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/avatar/upload", avatarUploadHandler, "POST")
	registerRouterFunc("/user/{handle:[a-zA-Z0-9-_]+}/promote", promoteHandler, "POST")

	registerRouterFunc("/user_search/{handle:[a-zA-Z0-9-_]+}", userSearchHandler, "GET")
}
