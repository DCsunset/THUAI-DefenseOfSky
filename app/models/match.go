package models

type Match struct {
	Id      int32
	Contest int32
	Report  string

	Rel struct {
		Contest Contest
		Parties []Submission
	}
}

type MatchParty struct {
	Match      int32
	Submission int32

	Rel struct {
		Match      Match
		Submission Submission
	}
}

func init() {
	registerSchema("match",
		"id SERIAL PRIMARY KEY",
		"contest INTEGER NOT NULL REFERENCES contest(id)",
		"report TEXT NOT NULL DEFAULT ''",
	)
	registerSchema("match_party",
		"match INTEGER NOT NULL REFERENCES match(id)",
		"submission INTEGER NOT NULL REFERENCES submission(id)",
	)
}

func (m *Match) Create() error {
	// TODO: Combine into an transaction
	err := db.QueryRow("INSERT INTO "+
		"match(contest, report) "+
		"VALUES ($1, $2) RETURNING id",
		m.Contest,
		m.Report,
	).Scan(&m.Id)
	if err != nil {
		return err
	}

	// Create MatchParty records
	for i, s := range m.Rel.Parties {
		_, err := db.Exec("INSERT INTO "+
			"match_party(match, submission) VALUES ($1, $2)",
			m.Id, s.Id)
		if err != nil {
			return err
		}
		err = s.Read()
		if err != nil {
			return err
		}
		err = s.LoadRel()
		if err != nil {
			return err
		}
		m.Rel.Parties[i] = s
	}

	return nil
}

func (m *Match) ShortRepresentation() map[string]interface{} {
	parties := []map[string]interface{}{}
	for _, p := range m.Rel.Parties {
		parties = append(parties, p.ShortRepresentation())
	}
	return map[string]interface{}{
		"id":      m.Id,
		"parties": parties,
	}
}

func (m *Match) Representation() map[string]interface{} {
	r := m.ShortRepresentation()
	r["report"] = m.Report
	return r
}

func (m *Match) Read() error {
	err := db.QueryRow("SELECT "+
		"contest, report "+
		"FROM match WHERE id = $1", m.Id,
	).Scan(
		&m.Contest,
		&m.Report,
	)
	return err
}

func ReadByContest(cid int32) ([]Match, error) {
	rows, err := db.Query("SELECT id FROM match WHERE contest = $1", cid)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	ms := []Match{}
	for rows.Next() {
		m := Match{Contest: cid}
		err := rows.Scan(&m.Id)
		if err != nil {
			return nil, err
		}
		// TODO: Optimize
		m.LoadRel()
		ms = append(ms, m)
	}
	return ms, rows.Err()
}

func (m *Match) LoadRel() error {
	m.Rel.Contest.Id = m.Contest
	if err := m.Rel.Contest.Read(); err != nil {
		return err
	}

	// Find out all parties
	rows, err := db.Query("SELECT submission FROM match_party "+
		"WHERE match = $1", m.Id)
	if err != nil {
		return err
	}
	defer rows.Close()
	m.Rel.Parties = []Submission{}
	for rows.Next() {
		// TODO: Optimize
		s := Submission{}
		if err := rows.Scan(&s.Id); err != nil {
			return err
		}
		if err := s.Read(); err != nil {
			return err
		}
		if err := s.LoadRel(); err != nil {
			return err
		}
		m.Rel.Parties = append(m.Rel.Parties, s)
	}
	return rows.Err()
}

func (m *Match) Update() error {
	// TODO
	return nil
}
