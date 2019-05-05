const VISIBILITY_ICON = {
    public: 'public',
    private: 'lock_outline',
};

const ROLE = {
    maintainer: 'Maintainer',
    test_developer: 'Test developer',
    tester: 'Tester',
};

function string_avatar(string) {
    const words = string.split(" ").slice(0, 2);
    return words.map((word) => {
        return word[0];
    }).join('');
}

const project_list_element_template = (project) => `
<li class="collection-item avatar">
    <i class="circle">${string_avatar(project.title)}</i>
    <a class="title black-text" href="${project.web_url}">${project.title}</a>
    <i class="material-icons tiny">${VISIBILITY_ICON[project.visibility]}</i>
    <span class="role new badge" data-badge-caption="${ROLE[project.permissions.role]}"></span>
    <p>Project description</p>
</li>
`;

const test_plan_list_element_template = (test_plan) => `
<li class="collection-item avatar">
    <i class="circle">${string_avatar(test_plan.title)}</i>
    <a class="title black-text" href="#">${test_plan.title}</a>
    <p>Current build: ${test_plan.current_build.title}</p>
    <span class="role new badge" data-badge-caption="Passed">${test_plan.current_build.passed}</span>
    <span class="role new badge" data-badge-caption="Failed">${test_plan.current_build.failed}</span>
    <span class="role new badge" data-badge-caption="Not run">${test_plan.current_build.not_run}</span>
    <span class="badge" data-badge-caption="">Last update: ${test_plan.last_update}</span>
</li>
`;



function add_project_list_element(project, container_id) {
    $(`#${container_id}`).append(project_list_element_template(project));
}

function add_test_plan_list_element(test_plan, container_id) {
    $(`#${container_id}`).append(test_plan_list_element_template(test_plan));
}
