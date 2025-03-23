import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
def is_valid_format(df):
    expected_columns = [
        "PID", "Allocation_A", "Allocation_B", "Allocation_C", 
        "Max_A", "Max_B", "Max_C", "Available_A", "Available_B", "Available_C", 
        "Need_A", "Need_B", "Need_C"
    ]
    return list(df.columns) == expected_columns

def find_all_safe_sequences(available, allocation, maximum):
    work = available.astype(int).copy()
    finish = [False] * len(allocation)
    safe_sequences = []
    reasoning_paths = []

    def explore_paths(path, work, finish, reasoning_steps):
        if len(path) == len(allocation):
            safe_sequences.append(path[:])
            reasoning_paths.append(reasoning_steps[:])
            return
        
        for i in range(len(allocation)):
            if not finish[i] and all((maximum[i] - allocation[i]) <= work):
                new_work = work + allocation[i].astype(int)
                new_finish = finish[:]
                new_finish[i] = True
                resource_addition = f"{work} + {allocation[i]} = {new_work}"
                new_reasoning_steps = reasoning_steps + [
                    f"Process P{i} can be executed as it needs {maximum[i] - allocation[i]} resources, which are available: {work}.",
                    f"After executing P{i}, available resources are updated: {resource_addition}."
                ]
                explore_paths(path + [i], new_work, new_finish, new_reasoning_steps)
    
    explore_paths([], work, finish, [])
    return safe_sequences, reasoning_paths

st.title("Banker's Algorithm - Safe Sequence Finder")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep="\t")
        
        if not is_valid_format(df):
            st.error("Invalid File Format")
        else:
            st.success("Valid File Format")
            
            allocation = df.iloc[:, 1:4].values.astype(int)
            maximum = df.iloc[:, 4:7].values.astype(int)
            available = df.iloc[0, 7:10].values.astype(int)
            
            safe_sequences, reasoning_paths = find_all_safe_sequences(available, allocation, maximum)
            
            if safe_sequences:
                st.success(f"Total Safe Sequences Found: {len(safe_sequences)}")
                selected_sequence = st.selectbox(
                    "Select a Safe Sequence to Visualize", 
                    [" → ".join([f"P{p}" for p in seq]) for seq in safe_sequences]
                )
                
                selected_idx = [" → ".join([f"P{p}" for p in seq]) for seq in safe_sequences].index(selected_sequence)
                reasoning_steps = reasoning_paths[selected_idx]
                chosen_path = safe_sequences[selected_idx]
                
                st.subheader("Step-by-Step Execution Visualization")
                if "step_idx" not in st.session_state:
                    st.session_state.step_idx = 0
                
                # Store executed processes
                executed_processes = set()

                df_display = df.copy()
                available_copy = available.copy()
                step_idx = st.session_state.step_idx

                for iteration in range(step_idx + 1):
                    st.markdown(f"### Iteration {iteration + 1}: Checking Processes Sequentially")
                    
                    for process_id in range(len(allocation)):  # Check all processes sequentially
                        if process_id in executed_processes:
                            st.info(f"ℹ️ Process P{process_id} is already executed and skipped.")
                            continue  # Skip already executed processes
                        
                        is_current_process = process_id == chosen_path[iteration]

                        def highlight_rows(row):
                            if row.name == process_id:
                                return ['background-color: yellow'] * len(row)  # Highlight current process
                            elif row.name in executed_processes:
                                return ['background-color: lightgreen'] * len(row)  # Mark executed processes
                            return [''] * len(row)

                        st.dataframe(df_display.style.apply(highlight_rows, axis=1))

                        need = df.iloc[process_id, 10:13].values.astype(int)

                        if all(need <= available_copy):  
                            if is_current_process:
                                st.success(f"✅ P{process_id} can execute as its need {need} is ≤ available {available_copy}.")
                                allocation_values = df.iloc[process_id, 1:4].values.astype(int)
                                updated_available = available_copy + allocation_values  # Release resources
                                st.info(f"🔄 Available resources updated: {available_copy} + {allocation_values} = {updated_available}.")
                                available_copy = updated_available  # Update available resources for next iteration
                                df_display.iloc[0, 7:10] = available_copy  # Update displayed table values
                                executed_processes.add(process_id)  # Mark as executed
                                st.write(f"Process P{process_id} executed successfully ✅")
                            else:
                                st.info(f"ℹ️ P{process_id} could be executed as its need {need} is ≤ available {available_copy}, but it's not in this path step.")
                        else:
                            st.warning(f"❌ P{process_id} cannot execute as its need {need} is greater than available {available_copy}.")

                    if len(executed_processes) == len(chosen_path):
                        st.success("🎉 Path Completed: All processes executed successfully!")
                        break

                if len(executed_processes) < len(chosen_path):
                    if st.button("Next Step", key="next_step_button", help="Click to proceed to the next step", use_container_width=True):
                        if st.session_state.step_idx < len(chosen_path):
                            st.session_state.step_idx += 1
                        else:
                            st.session_state.step_idx = 0  # Reset if at the end
            else:
                st.error("No safe sequences found. The system is in an unsafe state.")
    except Exception as e:
        st.error("Error processing file: " + str(e))
