local count = 2
local su_id = get_id('su')

function on_submission(all, from)
    print('Submission', from)
end

function on_timer(all)
    count = count + 1
    if count < 3 then return end
    count = 0
    print('Superuser has ID ' .. tostring(su_id))
    print('Creating matches for contest #0')
    print('Number of participants with delegates ' .. tostring(#all))
    local tab={}
    local index=1
    while #all~=0 do
        local n=math.random(0,#all)
        if all[n]~=nil then
            tab[index]=all[n]
            table.remove(all,n)
            index=index+1
        end
    end
    all=tab
    for i = 1, #all do
        print(string.format('Contestant %s (%d), rating %d, performance "%s"',
            all[i].handle, all[i].id, all[i].rating, all[i].performance))
        if i > 1 then create_match(all[i].id, all[i - 1].id) end
    end
end

function on_manual(all, arg)
    print('Manual', arg)
end

function update_stats(report, par)
    print('Update with ' .. tostring(#par) .. ' parties')
    print(report)
    local index1=string.find( report,"player0",1)+10;
    local index2=string.find(report,"player1",1)+10;
    local index3=string.find( report,"replay", 1)-3;
    print(index1,index2,index3)

    local player0=string.sub(report, index1,index2-14)
    print(player0)
    local player1=string.sub(report,index2,index3-1);
    print(player1)

    if par[0]
    for i = 1, #par do
        print(i, par[i].rating, par[i].performance)
        if i==1 then
            par[i].rating=par[i].rating+player0
        elseif i==2 then
            par[i].rating=par[i].rating+player1
        else
            print('No Player')
        end
        par[i].performance = 'Total Points: ' .. tostring(par[i].rating)
    end
end