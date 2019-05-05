const VISIBILITY_ICON = {
    public: 'public',
    private: 'lock_outline',
};

const ROLE = {
    maintainer: 'Maintainer',
    test_developer: 'Test developer',
    tester: 'Tester',
};

function project_string_avatar(string) {
    const words = string.split(" ").slice(0, 2);
    return words.map((word) => {
        return word[0];
    }).join('');
}

const project_list_element_template = (project) => `
<li class="collection-item avatar">
    <i class="circle">${project_string_avatar(project.title)}</i>
    <a class="title black-text" href="${project.web_url}">${project.title}</a>
    <i class="material-icons tiny">${VISIBILITY_ICON[project.visibility]}</i>
    <span class="role new badge" data-badge-caption="${ROLE[project.permissions.role]}"></span>
    <p>Project description</p>
</li>
`;


function add_project_list_element(project, container_id) {
    $(`#${container_id}`).append(project_list_element_template(project));
}
